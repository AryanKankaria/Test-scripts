import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')


class TestOldTokenInvalidation:

    def test_bearer_token_from_old_session_fails(self, api_session):
        login1 = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        old_token = api_session.cookies.get('sid')
        
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        new_session = requests.Session()
        headers = {'Authorization': f'Bearer {old_token}'}
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 401

    def test_concurrent_logins_invalidate_earlier_session(self, api_session):
        session1 = requests.Session()
        session2 = requests.Session()
        
        login1 = session1.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login1.status_code == 200
        token1 = session1.cookies.get('sid')
        
        login2 = session2.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login2.status_code == 200
        token2 = session2.cookies.get('sid')
        
        response1 = session1.get(f'{BASE_URL}/auth/verify')
        response2 = session2.get(f'{BASE_URL}/auth/verify')
        
        assert response1.status_code == 401
        assert response2.status_code == 200


class TestBearerTokenVariations:

    @pytest.mark.parametrize('prefix', ['bearer', 'BEARER', 'BeArEr'])
    def test_bearer_keyword_is_case_insensitive(self, api_session, prefix):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login_response.status_code == 200
        token = api_session.cookies.get('sid')

        new_session = requests.Session()
        response = new_session.get(
            f'{BASE_URL}/auth/verify',
            headers={'Authorization': f'{prefix} {token}'}
        )
        assert response.status_code == 200

    def test_other_authorization_schemes_fail(self, api_session):
        token = 'dummy_token_12345'
        
        new_session = requests.Session()
        
        headers = {'Authorization': f'Basic {token}'}
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 401
        
        headers = {'Authorization': f'Digest {token}'}
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 401
        
        headers = {'Authorization': f'Bearer {token}'}
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 401

    def test_bearer_token_double_spaces(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login_response.status_code == 200
        token = api_session.cookies.get('sid')
        
        new_session = requests.Session()
        headers = {'Authorization': f'Bearer  {token}'}
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 200

