import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')


class TestLogoutEdgeCases:

    def test_logout_with_bearer_token_in_header(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        token = api_session.cookies.get('sid')
        
        new_session = requests.Session()
        headers = {'Authorization': f'Bearer {token}'}
        response = new_session.post(f'{BASE_URL}/auth/logout', headers=headers)
        assert response.status_code == 200
        
        # Verify session is actually invalidated
        response_verify = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response_verify.status_code == 401

    def test_logout_multiple_times_same_session(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        response1 = api_session.post(f'{BASE_URL}/auth/logout')
        assert response1.status_code == 200
        
        response2 = api_session.post(f'{BASE_URL}/auth/logout')
        assert response2.status_code == 200

    def test_logout_returns_ok_true(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        response = api_session.post(f'{BASE_URL}/auth/logout')
        assert response.status_code == 200        
        # Verify session cookie is actually invalidated
        response_verify = api_session.get(f'{BASE_URL}/auth/verify')
        assert response_verify.status_code == 401        
        assert response.json()['ok'] is True


class TestLogoutWithCookie:

    def test_logout_invalidates_session_cookie(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        response1 = api_session.get(f'{BASE_URL}/auth/verify')
        assert response1.status_code == 200
        
        api_session.post(f'{BASE_URL}/auth/logout')
        
        response2 = api_session.get(f'{BASE_URL}/auth/verify')
        assert response2.status_code == 401

    def test_logout_subsequent_requests_fail(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        api_session.post(f'{BASE_URL}/auth/logout')
        
        for i in range(3):
            response = api_session.get(f'{BASE_URL}/auth/verify')
            assert response.status_code == 401

