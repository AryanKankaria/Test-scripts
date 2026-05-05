import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')


class TestResponseSecurityFields:

    def test_login_response_excludes_password(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        user = response.json()['user']
        assert 'password' not in user

    def test_login_response_excludes_password_hash(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        user = response.json()['user']
        assert 'password_hash' not in user

    def test_auth_verify_returns_user_data(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        
        response = api_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 200
        data = response.json()
        user = data.get('user', {})
        assert user.get('email') == TEST_USER_EMAIL
        assert 'id' in user 


