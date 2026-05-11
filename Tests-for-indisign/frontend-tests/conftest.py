import pytest
import os
import psycopg2
import bcrypt
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse
from playwright.sync_api import BrowserType

# Load shared env from Tests-for-indisign/.env
load_dotenv(Path(__file__).parent.parent / '.env')

APP_URL             = os.getenv('APP_URL',              'http://localhost:4200')
BASE_URL            = os.getenv('BASE_URL',             'http://localhost:3000')
DATABASE_URL        = os.getenv('DATABASE_URL',         'postgres://postgres:1234@localhost:5432/indisign')
TEST_USER_EMAIL     = os.getenv('TEST_USER_EMAIL',      'testuser@example.com')
TEST_USER_PASSWORD  = os.getenv('TEST_USER_PASSWORD',   'TestPassword@123')
PENDING_USER_EMAIL  = os.getenv('PENDING_USER_EMAIL',   'pending@example.com')
PENDING_USER_PASSWORD = os.getenv('PENDING_USER_PASSWORD', 'PendingPass@123')


@pytest.fixture(scope="module")
def browser(browser_type: BrowserType, browser_type_launch_args):
    """Single browser instance shared across all tests in a module."""
    b = browser_type.launch(**browser_type_launch_args)
    yield b
    b.close()


@pytest.fixture(scope="function")
def page(browser, browser_context_args):
    """Fresh browser context per test — prevents session/cookie bleed between tests."""
    context = browser.new_context(**browser_context_args)
    pg = context.new_page()
    yield pg
    context.close()


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'slow: marks tests as slow due to multiple API calls (deselect with -m "not slow")'
    )
    config.addinivalue_line(
        'markers',
        'flow: marks full end-to-end flow tests intended for prod/UAT (deselect with -m "not flow")'
    )


def _db_connect():
    parsed = urlparse(DATABASE_URL)
    return psycopg2.connect(
        host=parsed.hostname or 'localhost',
        port=parsed.port or 5432,
        user=parsed.username or 'postgres',
        password=parsed.password or '1234',
        database=parsed.path.lstrip('/') or 'indisign',
    )


def _snapshot_test_user():
    """Return (password_hash,) if the test user exists in users, else None."""
    try:
        conn = _db_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE email = %s", (TEST_USER_EMAIL,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    except Exception as e:
        print(f"[WARNING] Could not snapshot test user: {e}")
        return False  # False = DB unreachable; skip restore


def _snapshot_pending_user():
    """Return (password_hash, otp_phone_attempts, otp_email_attempts) if the pending user
    exists in pending_users, else None."""
    try:
        conn = _db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash, otp_phone_attempts, otp_email_attempts "
            "FROM pending_users WHERE email = %s",
            (PENDING_USER_EMAIL,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    except Exception as e:
        print(f"[WARNING] Could not snapshot pending user: {e}")
        return False


def _ensure_pending_user_exists():
    """Ensure a pending (unverified) user exists in pending_users for OTP flow tests."""
    try:
        conn = _db_connect()
        cursor = conn.cursor()
        pw_hash = bcrypt.hashpw(PENDING_USER_PASSWORD.encode(), bcrypt.gensalt(10)).decode()
        cursor.execute("SELECT id FROM pending_users WHERE email = %s", (PENDING_USER_EMAIL,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE pending_users SET password_hash = %s WHERE email = %s",
                (pw_hash, PENDING_USER_EMAIL)
            )
        else:
            cursor.execute(
                "INSERT INTO pending_users (email, password_hash) VALUES (%s, %s)",
                (PENDING_USER_EMAIL, pw_hash)
            )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[WARNING] Could not ensure pending user: {e}")


def _ensure_test_user_exists():
    """Ensure a fully verified test user exists in users for login success tests."""
    try:
        conn = _db_connect()
        cursor = conn.cursor()
        pw_hash = bcrypt.hashpw(TEST_USER_PASSWORD.encode(), bcrypt.gensalt(10)).decode()
        cursor.execute("SELECT id FROM users WHERE email = %s", (TEST_USER_EMAIL,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE users SET password = %s WHERE email = %s",
                (pw_hash, TEST_USER_EMAIL)
            )
        else:
            cursor.execute(
                "INSERT INTO users (email, password, first_name, last_name, created_at) "
                "VALUES (%s, %s, %s, %s, NOW())",
                (TEST_USER_EMAIL, pw_hash, 'Test', 'User')
            )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[WARNING] Could not ensure test user: {e}")


@pytest.fixture(scope='session', autouse=True)
def setup_test_users():
    # Snapshot state before any test touches the DB
    original_test_user = _snapshot_test_user()
    original_pending_user = _snapshot_pending_user()

    _ensure_test_user_exists()
    _ensure_pending_user_exists()

    yield

    # Restore DB to exact pre-test state
    if original_test_user is False and original_pending_user is False:
        return  # DB was unreachable at snapshot time; skip restore

    try:
        conn = _db_connect()
        cursor = conn.cursor()

        # Remove sessions created during the test run
        cursor.execute(
            "DELETE FROM sessions WHERE user_id IN "
            "(SELECT id FROM users WHERE email = %s)",
            (TEST_USER_EMAIL,)
        )

        # Restore test user
        if original_test_user is None:
            cursor.execute("DELETE FROM users WHERE email = %s", (TEST_USER_EMAIL,))
        else:
            cursor.execute(
                "UPDATE users SET password = %s WHERE email = %s",
                (original_test_user[0], TEST_USER_EMAIL)
            )

        # Restore pending user
        if original_pending_user is None:
            cursor.execute("DELETE FROM pending_users WHERE email = %s", (PENDING_USER_EMAIL,))
        else:
            cursor.execute(
                "UPDATE pending_users SET password_hash = %s, "
                "otp_phone_attempts = %s, otp_email_attempts = %s "
                "WHERE email = %s",
                (*original_pending_user, PENDING_USER_EMAIL)
            )

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[WARNING] Could not restore DB state after tests: {e}")


@pytest.fixture(scope='session', autouse=True)
def clear_rate_limiting_session():
    """Clear login cooldowns once after all tests complete."""
    yield
    try:
        conn = _db_connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM login_cooldowns")
        cursor.execute(
            "DELETE FROM platform_logs WHERE action = 'login_failed' "
            "AND metadata->>'email' IN (%s, %s) "
            "AND created_at > NOW() - INTERVAL '24 hours'",
            (TEST_USER_EMAIL, PENDING_USER_EMAIL)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[WARNING] Could not clear rate limiting after session: {e}")


@pytest.fixture(autouse=True)
def clear_rate_limiting():
    """Clear login cooldowns before each test so rate limit state doesn't bleed between tests."""
    try:
        conn = _db_connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM login_cooldowns")
        cursor.execute(
            "DELETE FROM platform_logs WHERE action='login_failed' "
            "AND metadata->>'email' = %s AND created_at > NOW() - INTERVAL '24 hours'",
            (TEST_USER_EMAIL,)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[WARNING] Could not clear rate limiting: {e}")
    yield
