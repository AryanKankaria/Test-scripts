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

    def test_logout_clears_sid_cookie(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert 'sid' in api_session.cookies
        
        api_session.post(f'{BASE_URL}/auth/logout')
        
        response = api_session.get(f'{BASE_URL}/auth/me')
        assert response.status_code == 401

    def test_multiple_failed_logins_increase_cooldown(self, api_session):
        for i in range(6):
            api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': TEST_USER_EMAIL, 'password': 'wrong_password'}
            )
        
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 429

    def test_rate_limit_response_contains_retry_info(self, api_session):
        for i in range(5):
            api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': TEST_USER_EMAIL, 'password': 'wrong_pass'}
            )
        
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        if response.status_code == 429:
            data = response.json()
            assert 'error' in data
            assert 'retry_after_seconds' in data or 'cooldown_seconds' in data


class TestAuthValidation:

    def test_password_is_required(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL}
        )
        assert response.status_code == 400

    def test_email_is_required(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 400

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

    def test_empty_string_credentials_rejected(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': '', 'password': ''}
        )
        assert response.status_code == 400


class TestAuthAuditTrail:

    def test_successful_login_user_can_access_protected_endpoint(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        response = api_session.get(f'{BASE_URL}/auth/me')
        assert response.status_code == 200
        user = response.json()
        assert user['email'] == TEST_USER_EMAIL

    def test_failed_login_user_cannot_access_protected_endpoint(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': 'wrongpassword'}
        )
        
        response = api_session.get(f'{BASE_URL}/auth/me')
        assert response.status_code == 401

    def test_after_logout_user_cannot_access_protected_endpoint(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        api_session.post(f'{BASE_URL}/auth/logout')
        
        response = api_session.get(f'{BASE_URL}/auth/me')
        assert response.status_code == 401
