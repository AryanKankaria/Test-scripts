import pytest
import requests
import os
from dotenv import load_dotenv
import psycopg2
from pathlib import Path


load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')
TEAM_USER_EMAIL = os.getenv('TEAM_USER_EMAIL', 'teamuser@example.com')
TEAM_USER_PASSWORD = os.getenv('TEAM_USER_PASSWORD', 'TeamPass@123')
PENDING_USER_EMAIL = os.getenv('PENDING_USER_EMAIL', 'pending@example.com')
PENDING_USER_PASSWORD = os.getenv('PENDING_USER_PASSWORD', 'PendingPass@123')

backend_env_path = Path(__file__).parent.parent / 'indisign-backend' / '.env'
if backend_env_path.exists():
    load_dotenv(backend_env_path)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgres://postgres:1234@localhost:5432/indisign')


def _parse_db_url(url):
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'user': parsed.username or 'postgres',
        'password': parsed.password or '1234',
        'database': parsed.path.lstrip('/') or 'indisign'
    }


def _ensure_pending_user_exists():
    import bcrypt
    try:
        db_params = _parse_db_url(DATABASE_URL)
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        pending_password_hash = bcrypt.hashpw(PENDING_USER_PASSWORD.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')
        cursor.execute("SELECT id FROM pending_users WHERE email = %s", (PENDING_USER_EMAIL,))
        if cursor.fetchone():
            cursor.execute("UPDATE pending_users SET password_hash = %s WHERE email = %s",
                           (pending_password_hash, PENDING_USER_EMAIL))
            print(f"[SETUP] Updated pending user: {PENDING_USER_EMAIL}")
        else:
            cursor.execute(
                "INSERT INTO pending_users (email, password_hash) VALUES (%s, %s)",
                (PENDING_USER_EMAIL, pending_password_hash)
            )
            print(f"[SETUP] Created pending user: {PENDING_USER_EMAIL}")

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[WARNING] Could not ensure pending user exists: {e}")


def _ensure_test_user_exists():
    import bcrypt
    try:
        db_params = _parse_db_url(DATABASE_URL)
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Setup TEST_USER
        test_password_hash = bcrypt.hashpw(TEST_USER_PASSWORD.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')
        cursor.execute("SELECT id FROM users WHERE email = %s", (TEST_USER_EMAIL,))
        if cursor.fetchone():
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (test_password_hash, TEST_USER_EMAIL))
            print(f"[SETUP] Updated test user password: {TEST_USER_EMAIL}")
        else:
            cursor.execute(
                "INSERT INTO users (email, password, first_name, last_name, created_at) VALUES (%s, %s, %s, %s, NOW())",
                (TEST_USER_EMAIL, test_password_hash, 'Test', 'User')
            )
            print(f"[SETUP] Created test user: {TEST_USER_EMAIL}")
        
        # Setup TEAM_USER
        team_password_hash = bcrypt.hashpw(TEAM_USER_PASSWORD.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')
        cursor.execute("SELECT id FROM users WHERE email = %s", (TEAM_USER_EMAIL,))
        if cursor.fetchone():
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (team_password_hash, TEAM_USER_EMAIL))
            print(f"[SETUP] Updated team user password: {TEAM_USER_EMAIL}")
        else:
            cursor.execute(
                "INSERT INTO users (email, password, first_name, last_name, created_at) VALUES (%s, %s, %s, %s, NOW())",
                (TEAM_USER_EMAIL, team_password_hash, 'Team', 'User')
            )
            print(f"[SETUP] Created team user: {TEAM_USER_EMAIL}")
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[WARNING] Could not ensure test users exist: {e}")


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    _ensure_test_user_exists()
    _ensure_pending_user_exists()
    yield


@pytest.fixture
def api_session():
    session = requests.Session()
    yield session
    session.close()


@pytest.fixture
def authenticated_session(api_session):
    response = api_session.post(
        f'{BASE_URL}/auth/login',
        json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
    )
    if response.status_code == 200:
        yield api_session
    else:
        yield api_session
    api_session.close()


@pytest.fixture(scope='session')
def base_url():
    return BASE_URL


@pytest.fixture(autouse=True)
def clear_rate_limiting():
    """Clear all login_cooldowns and failed login records before each test to prevent rate limit accumulation."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 5432,
            user=parsed.username or 'postgres',
            password=parsed.password or '1234',
            database=parsed.path.lstrip('/') or 'indisign'
        )
        cursor = conn.cursor()
        
        # Clear cooldown records
        cursor.execute("DELETE FROM login_cooldowns")
        cooldown_count = cursor.rowcount
        
        # Clear failed login records for both test users in platform_logs (last 24 hours to be safe)
        cursor.execute(
            "DELETE FROM platform_logs WHERE action='login_failed' AND (metadata->>'email' = %s OR metadata->>'email' = %s) AND created_at > NOW() - INTERVAL '24 hours'",
            (TEST_USER_EMAIL, TEAM_USER_EMAIL)
        )
        failed_login_count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if cooldown_count > 0 or failed_login_count > 0:
            print(f"[CLEANUP] Cleared {cooldown_count} cooldown records, {failed_login_count} failed login records")
    except Exception as e:
        print(f"[WARNING] Could not clear rate limiting: {e}")
    yield


@pytest.fixture(scope='module', autouse=True)
def cleanup_cooldowns_after_module():
    """Clear login_cooldowns and failed login records after each test module/file completes."""
    yield
    try:
        from urllib.parse import urlparse
        parsed = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 5432,
            user=parsed.username or 'postgres',
            password=parsed.password or '1234',
            database=parsed.path.lstrip('/') or 'indisign'
        )
        cursor = conn.cursor()
        
        # Clear all cooldown records
        cursor.execute("DELETE FROM login_cooldowns")
        cooldown_count = cursor.rowcount
        
        # Clear failed login records for both test users in platform_logs
        cursor.execute(
            "DELETE FROM platform_logs WHERE action='login_failed' AND (metadata->>'email' = %s OR metadata->>'email' = %s)",
            (TEST_USER_EMAIL, TEAM_USER_EMAIL)
        )
        failed_login_count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[CLEANUP] After module: Cleared {cooldown_count} cooldown records, {failed_login_count} failed login records")
    except Exception as e:
        print(f"[WARNING] Could not clear cooldowns after module: {e}")
