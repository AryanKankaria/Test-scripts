import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')


class TestOldTokenInvalidation:

    def test_old_session_invalidated_after_new_login(self, api_session):
        response1 = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response1.status_code == 200
        token1 = api_session.cookies.get('sid')
        
        response2 = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response2.status_code == 200
        
        new_session = requests.Session()
        new_session.cookies.set('sid', token1)
        response = new_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401

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

    def test_bearer_token_lowercase(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login_response.status_code == 200
        token = api_session.cookies.get('sid')
        
        new_session = requests.Session()
        headers = {'Authorization': f'bearer {token}'}
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 200

    def test_bearer_token_uppercase(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login_response.status_code == 200
        token = api_session.cookies.get('sid')
        
        new_session = requests.Session()
        headers = {'Authorization': f'BEARER {token}'}
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 200

    def test_bearer_token_mixed_case(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login_response.status_code == 200
        token = api_session.cookies.get('sid')
        
        new_session = requests.Session()
        headers = {'Authorization': f'BeArEr {token}'}
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
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

