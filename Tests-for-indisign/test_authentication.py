import pytest
import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')


class TestLoginSuccess:

    def test_valid_login_returns_user_and_sets_cookie(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        assert 'user' in response.json()
        assert response.json()['user']['email'] == TEST_USER_EMAIL
        assert 'sid' in api_session.cookies

    def test_login_creates_valid_session(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login_response.status_code == 200
        
        response = api_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 200
        data = response.json()
        # Check for email in response - might be under 'email' or other keys
        assert 'email' in data or 'user' in data, f"Response missing user data: {data}"

    def test_login_removes_previous_sessions(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        old_sid = api_session.cookies.get('sid')

        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        new_sid = api_session.cookies.get('sid')

        assert old_sid != new_sid

        old_session = requests.Session()
        old_session.cookies.set('sid', old_sid)
        response = old_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401


class TestLoginFailure:

    def test_login_invalid_password(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': 'WrongPassword123'}
        )
        assert response.status_code == 401
        assert 'error' in response.json()

    def test_login_nonexistent_user(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'nonexistent@example.com', 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 401
        assert response.json()['error'] == 'invalid credentials'

    def test_login_missing_email(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 400

    def test_login_missing_password(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL}
        )
        assert response.status_code == 400

    def test_login_empty_credentials(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': '', 'password': ''}
        )
        assert response.status_code == 400


class TestRateLimiting:

    def test_rate_limit_after_failed_attempts(self, api_session):
        max_attempts = 11 # @todo: pull this number from the code itself.
        for i in range(max_attempts):
            response = api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': TEST_USER_EMAIL, 'password': f'WrongPassword{i}'}
            )
            assert response.status_code in [401, 429]

        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 429, f"Expected rate limit (429), got {response.status_code}"
        assert 'cooldown' in response.text.lower() or 'retry' in response.text.lower()

    def test_rate_limit_returns_retry_after(self, api_session):
        for i in range(11): # @todo: pull this number from the code itself.
            response = api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': TEST_USER_EMAIL, 'password': 'WrongPassword'}
            )
            assert response.status_code in [401, 429]

        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 429, f"Expected rate limit (429), got {response.status_code}"
        assert 'retry_after_seconds' in response.json() or 'cooldown_seconds' in response.json()


class TestLogout:

    def test_logout_clears_session(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        response = api_session.post(f'{BASE_URL}/auth/logout')
        assert response.status_code == 200
        assert response.json()['ok'] is True

    def test_logout_invalidates_cookie(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        api_session.post(f'{BASE_URL}/auth/logout')

        response = api_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401

    def test_logout_without_session(self, api_session):
        response = api_session.post(f'{BASE_URL}/auth/logout')
        assert response.status_code == 200


class TestSessionManagement:

    def test_request_without_session_cookie(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        api_session.cookies.clear()
        
        response = api_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401

    def test_request_with_authorization_header(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        token = login_response.cookies.get('sid')
        headers = {'Authorization': f'Bearer {token}'}
        
        new_session = requests.Session()
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 200

    def test_session_remains_valid_after_short_delay(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        first_request = api_session.get(f'{BASE_URL}/auth/verify')
        assert first_request.status_code == 200
        
        time.sleep(2)
        
        second_request = api_session.get(f'{BASE_URL}/auth/verify')
        assert second_request.status_code == 200


class TestAuthorizationErrors:

    def test_invalid_token_format(self, api_session):
        headers = {'Authorization': 'Bearer invalid_token_format'}
        response = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 401

    def test_missing_authorization_header_and_cookie(self, api_session):
        response = api_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401

