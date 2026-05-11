import pytest
import requests
import os
from dotenv import load_dotenv

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
        for i in range(11):
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
        data = response.json()
        assert 'error' in data
        assert 'retry_after_seconds' in data or 'cooldown_seconds' in data


class TestLogout:

    def test_logout_clears_session(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        response = api_session.post(f'{BASE_URL}/auth/logout')
        assert response.status_code == 200
        assert response.json()['ok'] is True

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


class TestAuthorizationErrors:

    def test_missing_authorization_header_and_cookie(self, api_session):
        response = api_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401


class TestFullLoginFlow:

    def test_login_verify_logout_verify(self, api_session):
        """Full cycle: login → session works → logout → session gone."""
        # Step 1: login
        login = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD},
        )
        assert login.status_code == 200
        assert 'sid' in api_session.cookies

        # Step 2: session is valid
        verify_before = api_session.get(f'{BASE_URL}/auth/verify')
        assert verify_before.status_code == 200

        # Step 3: logout
        logout = api_session.post(f'{BASE_URL}/auth/logout')
        assert logout.status_code == 200
        assert logout.json().get('ok') is True

        # Step 4: session is gone
        verify_after = api_session.get(f'{BASE_URL}/auth/verify')
        assert verify_after.status_code == 401

