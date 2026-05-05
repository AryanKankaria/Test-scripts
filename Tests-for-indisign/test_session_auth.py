import pytest
import requests
import os
from dotenv import load_dotenv
from http.cookiejar import Cookie
import time

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')


class TestSessionCookie:

    def test_login_sets_httponly_cookie(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        assert 'sid' in api_session.cookies

        # Verify the sid cookie carries the HttpOnly flag
        try:
            set_cookie_headers = response.raw.headers.getlist('Set-Cookie')
        except AttributeError:
            set_cookie_headers = [response.headers.get('Set-Cookie', '')]
        sid_header = next((h for h in set_cookie_headers if 'sid=' in h), '')
        assert sid_header, "sid Set-Cookie header not found in response"
        assert 'httponly' in sid_header.lower(), f"sid cookie missing HttpOnly flag: {sid_header}"

    def test_cookie_persists_across_requests(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login_response.status_code == 200
        
        first_response = api_session.get(f'{BASE_URL}/auth/verify')
        assert first_response.status_code == 200
        
        second_response = api_session.get(f'{BASE_URL}/auth/verify')
        assert second_response.status_code == 200

    def test_multiple_sessions_invalidate_previous(self, api_session):
        login1 = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login1.status_code == 200
        first_cookie = api_session.cookies.get('sid')

        login2 = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login2.status_code == 200
        second_cookie = api_session.cookies.get('sid')

        assert first_cookie != second_cookie

        old_session = requests.Session()
        old_session.cookies.set('sid', first_cookie)
        response = old_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401

    def test_logout_removes_session(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        api_session.post(f'{BASE_URL}/auth/logout')
        
        response = api_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401


class TestBearerTokenAuth:

    def test_login_with_bearer_token_in_header(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        token = login_response.cookies.get('sid')
        
        new_session = requests.Session()
        headers = {'Authorization': f'Bearer {token}'}
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 200

    def test_bearer_token_without_bearer_prefix_passes(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        token = api_session.cookies.get('sid')
        
        new_session = requests.Session()
        headers = {'Authorization': token}
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 200
        # The reason this passes is because the bearer prefix is stripped off in the backend,
        # so it accepts the token if it is sent without the bearer prefix too.

    def test_invalid_bearer_token_fails(self, api_session):
        headers = {'Authorization': 'Bearer invalid_token_12345'}
        response = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 401


class TestSessionExpiry:

    def test_session_continues_to_be_valid(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        for _ in range(3):
            response = api_session.get(f'{BASE_URL}/auth/verify')
            assert response.status_code == 200
            time.sleep(1)

    def test_session_remains_valid_after_short_delay(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        response1 = api_session.get(f'{BASE_URL}/auth/verify')
        assert response1.status_code == 200
        
        time.sleep(2)
        
        response2 = api_session.get(f'{BASE_URL}/auth/verify')
        assert response2.status_code == 200
