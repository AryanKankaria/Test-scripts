import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
PENDING_USER_EMAIL = os.getenv('PENDING_USER_EMAIL', 'pending@example.com')
PENDING_USER_PASSWORD = os.getenv('PENDING_USER_PASSWORD', 'PendingPass@123')


class TestPendingUserLogin:

    def test_pending_user_cannot_login(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': PENDING_USER_EMAIL, 'password': PENDING_USER_PASSWORD}
        )
        assert response.status_code == 401
##      assert 'pending' in response.json().get('error', '').lower()
##      This can be added in V2 when we have a different message for pending users. 


    def test_pending_user_returns_pending_id(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': PENDING_USER_EMAIL, 'password': PENDING_USER_PASSWORD}
        )
        assert response.status_code == 401
        data = response.json()
        assert 'pending_id' in data
        assert 'not verified' in data.get('error', '').lower()


    def test_pending_user_no_session_created(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': PENDING_USER_EMAIL, 'password': PENDING_USER_PASSWORD}
        )
        
        response = api_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401

    def test_pending_user_no_cookie_set(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': PENDING_USER_EMAIL, 'password': PENDING_USER_PASSWORD}
        )
        
        assert response.status_code == 401
        assert 'sid' not in api_session.cookies
