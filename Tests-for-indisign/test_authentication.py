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
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        response = api_session.get(f'{BASE_URL}/auth/me')
        assert response.status_code == 200
        assert response.json()['email'] == TEST_USER_EMAIL

    def test_login_removes_previous_sessions(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        first_login_cookies = dict(api_session.cookies)

        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        second_login_cookies = dict(api_session.cookies)

        assert first_login_cookies != second_login_cookies


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
        max_attempts = 5
        for i in range(max_attempts):
            response = api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': TEST_USER_EMAIL, 'password': f'WrongPassword{i}'}
            )
            assert response.status_code == 401

        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 429

    def test_rate_limit_returns_retry_after(self, api_session):
        for i in range(5):
            api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': TEST_USER_EMAIL, 'password': 'WrongPassword'}
            )

        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 429
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

        response = api_session.get(f'{BASE_URL}/auth/me')
        assert response.status_code == 401

    def test_logout_without_session(self, api_session):
        response = api_session.post(f'{BASE_URL}/auth/logout')
        assert response.status_code == 200


class TestSessionManagement:

    def test_request_with_expired_session(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        api_session.cookies.clear()
        
        response = api_session.get(f'{BASE_URL}/auth/me')
        assert response.status_code == 401

    def test_request_with_authorization_header(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        token = login_response.cookies.get('sid')
        headers = {'Authorization': f'Bearer {token}'}
        
        new_session = requests.Session()
        response = new_session.get(f'{BASE_URL}/auth/me', headers=headers)
        assert response.status_code == 200

    def test_session_sliding_window(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        first_request = api_session.get(f'{BASE_URL}/auth/me')
        assert first_request.status_code == 200
        
        time.sleep(2)
        
        second_request = api_session.get(f'{BASE_URL}/auth/me')
        assert second_request.status_code == 200


class TestAuthorizationErrors:

    def test_invalid_token_format(self, api_session):
        headers = {'Authorization': 'Bearer invalid_token_format'}
        response = api_session.get(f'{BASE_URL}/auth/me', headers=headers)
        assert response.status_code == 401

    def test_tampered_session_token(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        api_session.cookies['sid'] = 'tampered_token_data'
        
        response = api_session.get(f'{BASE_URL}/auth/me')
        assert response.status_code == 401

    def test_missing_authorization_header_and_cookie(self, api_session):
        response = api_session.get(f'{BASE_URL}/auth/me')
        assert response.status_code == 401
