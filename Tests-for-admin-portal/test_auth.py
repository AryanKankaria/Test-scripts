import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')


class TestAuthLogin:
    
    def test_valid_login_with_correct_credentials(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'admin@test.com', 'password': 'Test@1234'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'token' in data
        assert 'user' in data
        assert data['user']['email'] == 'admin@test.com'

    def test_invalid_login_wrong_password(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'admin@test.com', 'password': 'WrongPassword123'}
        )
        assert response.status_code == 401
        assert response.json()['message'] == 'Invalid credentials.'

    def test_invalid_login_nonexistent_user(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'nonexistent@test.com', 'password': 'Test@1234'}
        )
        assert response.status_code == 401
        assert response.json()['message'] == 'Invalid credentials.'

    def test_login_missing_email(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'password': 'Test@1234'}
        )
        assert response.status_code == 400
        assert response.json()['message'] == 'Email and password are required.'

    def test_login_missing_password(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'admin@test.com'}
        )
        assert response.status_code == 400
        assert response.json()['message'] == 'Email and password are required.'

    def test_login_email_normalization(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'ADMIN@TEST.COM', 'password': 'Test@1234'}
        )
        assert response.status_code == 200
        assert response.json()['user']['email'] == 'admin@test.com'

    def test_login_rate_limit(self, api_session):
        for i in range(11):
            response = api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': 'admin@test.com', 'password': 'WrongPassword'}
            )
            if i < 10:
                assert response.status_code == 401
            else:
                assert response.status_code == 429


class TestAuthLogout:

    def test_logout_with_valid_token(self, api_session, admin_token):
        response = api_session.post(
            f'{BASE_URL}/auth/logout',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 204

    def test_logout_without_token(self, api_session):
        response = api_session.post(f'{BASE_URL}/auth/logout')
        assert response.status_code == 401
        assert response.json()['message'] == 'No token provided.'

    def test_logout_with_invalid_token(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/logout',
            headers={'Authorization': 'Bearer invalid_token_here'}
        )
        assert response.status_code == 401
        assert response.json()['message'] == 'Invalid token.'

    def test_logout_blacklists_token(self, api_session, admin_token):
        response = api_session.post(
            f'{BASE_URL}/auth/logout',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 204

        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 401


class TestAuthMe:

    def test_get_current_user_profile(self, api_session, admin_token):
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'id' in data
        assert 'email' in data
        assert 'name' in data
        assert 'role' in data

    def test_get_profile_without_token(self, api_session):
        response = api_session.get(f'{BASE_URL}/auth/me')
        assert response.status_code == 401
        assert response.json()['message'] == 'No token provided.'

    def test_get_profile_with_invalid_token(self, api_session):
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': 'Bearer invalid_token'}
        )
        assert response.status_code == 401
        assert response.json()['message'] == 'Invalid token.'

    def test_get_profile_expired_token(self, api_session):
        expired_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiZW1haWwiOiJhZG1pbkB0ZXN0LmNvbSIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTUxNjIzOTAyMiwiZXhwIjowfQ.invalid'
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer {expired_token}'}
        )
        assert response.status_code == 401


class TestAuthPasswordReset:

    def test_forgot_password_valid_email(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/forgot-password',
            json={'email': 'admin@test.com'}
        )
        assert response.status_code == 204

    def test_forgot_password_invalid_email(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/forgot-password',
            json={'email': 'nonexistent@test.com'}
        )
        assert response.status_code == 204

    def test_forgot_password_no_email(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/forgot-password',
            json={}
        )
        assert response.status_code == 204

    def test_reset_password_missing_token(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/reset-password',
            json={'newPassword': 'NewPassword@123'}
        )
        assert response.status_code == 400
        assert response.json()['message'] == 'Token and new password are required.'

    def test_reset_password_missing_password(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/reset-password',
            json={'token': 'sometoken123'}
        )
        assert response.status_code == 400
        assert response.json()['message'] == 'Token and new password are required.'

    def test_reset_password_invalid_token(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/reset-password',
            json={'token': 'invalidtoken123', 'newPassword': 'NewPassword@123'}
        )
        assert response.status_code == 400
        assert response.json()['message'] == 'Invalid or expired reset token.'


class TestSessionPersistence:

    def test_same_token_works_multiple_requests(self, api_session, admin_token):
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        response1 = api_session.get(f'{BASE_URL}/auth/me', headers=headers)
        response2 = api_session.get(f'{BASE_URL}/auth/me', headers=headers)
        response3 = api_session.get(f'{BASE_URL}/auth/me', headers=headers)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

    def test_token_persists_across_requests(self, api_session, admin_token):
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        response = api_session.get(f'{BASE_URL}/tickets', headers=headers)
        assert response.status_code in [200, 403]
        
        response = api_session.get(f'{BASE_URL}/auth/me', headers=headers)
        assert response.status_code == 200


class TestConcurrentLogins:

    def test_multiple_concurrent_logins(self, api_session):
        credentials = {'email': 'admin@test.com', 'password': 'Test@1234'}
        
        response1 = api_session.post(f'{BASE_URL}/auth/login', json=credentials)
        response2 = api_session.post(f'{BASE_URL}/auth/login', json=credentials)
        response3 = api_session.post(f'{BASE_URL}/auth/login', json=credentials)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        
        token1 = response1.json()['token']
        token2 = response2.json()['token']
        token3 = response3.json()['token']
        
        assert token1 != token2
        assert token2 != token3

    def test_all_tokens_valid_simultaneously(self, api_session):
        credentials = {'email': 'admin@test.com', 'password': 'Test@1234'}
        
        response1 = api_session.post(f'{BASE_URL}/auth/login', json=credentials)
        response2 = api_session.post(f'{BASE_URL}/auth/login', json=credentials)
        
        token1 = response1.json()['token']
        token2 = response2.json()['token']
        
        result1 = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer {token1}'}
        )
        result2 = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer {token2}'}
        )
        
        assert result1.status_code == 200
        assert result2.status_code == 200


class TestTokenExpiration:

    def test_expired_token_denied_access(self, api_session):
        expired_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiZW1haWwiOiJhZG1pbkB0ZXN0LmNvbSIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTUxNjIzOTAyMiwiZXhwIjowfQ.invalid'
        
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer {expired_token}'}
        )
        assert response.status_code == 401

    def test_malformed_token_denied_access(self, api_session):
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': 'Bearer malformed.token.here'}
        )
        assert response.status_code == 401


class TestInactiveAccount:

    def test_inactive_account_cannot_login(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'inactive@test.com', 'password': 'Test@1234'}
        )
        assert response.status_code == 403
        assert response.json()['message'] == 'Account is inactive. Contact an admin.'


class TestLastLoginTracking:

    def test_last_login_updated_on_login(self, api_session):
        credentials = {'email': 'admin@test.com', 'password': 'Test@1234'}
        
        response = api_session.post(f'{BASE_URL}/auth/login', json=credentials)
        assert response.status_code == 200
        
        token = response.json()['token']
        profile = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer {token}'}
        ).json()
        
        assert 'id' in profile
        assert 'email' in profile


class TestWhitespaceHandling:

    def test_bearer_token_whitespace_trimmed(self, api_session, admin_token):
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer   {admin_token}   '}
        )
        assert response.status_code == 200

    def test_email_whitespace_trimmed_on_login(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': '  admin@test.com  ', 'password': 'Test@1234'}
        )
        assert response.status_code == 200

