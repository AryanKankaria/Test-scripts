import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')


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


@pytest.fixture
def base_url():
    return BASE_URL
