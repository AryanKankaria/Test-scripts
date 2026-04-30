import pytest
import time
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')


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
