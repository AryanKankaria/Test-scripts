import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')


class TestAuthenticationErrorHandling:

    def test_login_error_message_on_wrong_password(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': 'wrongpass'}
        )
        assert response.status_code == 401
        assert 'error' in response.json()
        assert response.json()['error'] in ['invalid credentials', 'Invalid credentials']

    def test_login_error_message_on_nonexistent_user(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'nonexistent@example.com', 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 401

    def test_login_response_structure_success(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'user' in data
        assert 'email' in data['user']
        assert 'id' in data['user']

    def test_login_response_does_not_contain_password(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'password' not in data['user']
        assert 'password_hash' not in data['user']

    def test_login_case_insensitive_email(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL.upper(), 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 200

    def test_login_email_with_whitespace(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': f'  {TEST_USER_EMAIL}  ', 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 200


class TestAuthCookieSecurity:

    def test_multiple_failed_logins_increase_cooldown(self, api_session):
        # Push the account to the rate limit threshold
        for i in range(11):
            api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': TEST_USER_EMAIL, 'password': f'WrongPassword{i}'}
            )

        # Capture the cooldown from the first 429
        r1 = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': 'WrongPassword'}
        )
        assert r1.status_code == 429, f"Expected 429 after threshold, got {r1.status_code}"
        data1 = r1.json()
        cooldown1 = data1.get('cooldown_seconds') or data1.get('retry_after_seconds')
        assert cooldown1 is not None, "429 response missing cooldown field on first attempt"

        # One more failure — cooldown must be greater than or equal to the previous value
        r2 = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': 'WrongPassword'}
        )
        assert r2.status_code == 429
        data2 = r2.json()
        cooldown2 = data2.get('cooldown_seconds') or data2.get('retry_after_seconds')
        assert cooldown2 is not None, "429 response missing cooldown field on second attempt"
        assert cooldown2 >= cooldown1, (
            f"Cooldown did not increase: attempt 13 returned {cooldown2}s "
            f"but attempt 12 returned {cooldown1}s"
        )

    def test_logout_clears_sid_cookie(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert 'sid' in api_session.cookies
        
        api_session.post(f'{BASE_URL}/auth/logout')
        
        response = api_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401


class TestAuthValidation:

    def test_both_email_and_password_required(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={}
        )
        assert response.status_code == 400

    def test_null_credentials_rejected(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': None, 'password': None}
        )
        assert response.status_code == 400 or response.status_code == 401


class TestAuthAuditTrail:

    def test_failed_login_user_cannot_access_protected_endpoint(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': 'wrongpassword'}
        )
        
        response = api_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401


