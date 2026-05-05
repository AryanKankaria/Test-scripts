import pytest
import requests
import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
TEST_ADMIN_EMAIL = os.getenv('TEST_ADMIN_EMAIL', 'admin@test.com')
TEST_ADMIN_PASSWORD = os.getenv('TEST_ADMIN_PASSWORD', 'Test@1234')
TEST_EDITOR_EMAIL = os.getenv('TEST_EDITOR_EMAIL', 'editor@test.com')
TEST_EDITOR_PASSWORD = os.getenv('TEST_EDITOR_PASSWORD', 'Test@1234')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'admin_portal_test')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')


@pytest.fixture
def api_session():
    session = requests.Session()
    yield session
    session.close()


@pytest.fixture
def admin_token(api_session):
    response = api_session.post(
        f'{BASE_URL}/auth/login',
        json={'email': TEST_ADMIN_EMAIL, 'password': TEST_ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json()['token']
    return None


@pytest.fixture
def editor_token(api_session):
    response = api_session.post(
        f'{BASE_URL}/auth/login',
        json={'email': TEST_EDITOR_EMAIL, 'password': TEST_EDITOR_PASSWORD}
    )
    if response.status_code == 200:
        return response.json()['token']
    return None


@pytest.fixture
def admin_headers(admin_token):
    return {'Authorization': f'Bearer {admin_token}'}


@pytest.fixture
def editor_headers(editor_token):
    return {'Authorization': f'Bearer {editor_token}'}


@pytest.fixture
def db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        yield conn
        conn.close()
    except psycopg2.Error as e:
        pytest.skip(f"Database connection failed: {str(e)}")


@pytest.fixture
def db_cursor(db_connection):
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()


@pytest.fixture
def db_query(db_cursor):
    def execute_query(query_str, params=None):
        try:
            db_cursor.execute(query_str, params or ())
            db_connection.commit()
            return db_cursor.fetchall()
        except psycopg2.Error as e:
            db_connection.rollback()
            raise e
    return execute_query


@pytest.fixture
def db_transaction(db_connection):
    db_connection.autocommit = False
    yield db_connection
    db_connection.rollback()

