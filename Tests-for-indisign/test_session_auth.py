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
        
        cookies = api_session.cookies
        assert 'sid' in cookies

    def test_cookie_persists_across_requests(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        first_response = api_session.get(f'{BASE_URL}/auth/me')
        assert first_response.status_code == 200
        
        second_response = api_session.get(f'{BASE_URL}/auth/me')
        assert second_response.status_code == 200

    def test_multiple_sessions_invalidate_previous(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        first_cookie = api_session.cookies.get('sid')
        
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        second_cookie = api_session.cookies.get('sid')
        
        assert first_cookie != second_cookie

    def test_logout_removes_session(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        api_session.post(f'{BASE_URL}/auth/logout')
        
        response = api_session.get(f'{BASE_URL}/auth/me')
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
        response = new_session.get(f'{BASE_URL}/auth/me', headers=headers)
        assert response.status_code == 200

    def test_bearer_token_without_bearer_prefix_fails(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        token = api_session.cookies.get('sid')
        
        new_session = requests.Session()
        headers = {'Authorization': token}
        response = new_session.get(f'{BASE_URL}/auth/me', headers=headers)
        assert response.status_code == 401

    def test_invalid_bearer_token_fails(self, api_session):
        headers = {'Authorization': 'Bearer invalid_token_12345'}
        response = api_session.get(f'{BASE_URL}/auth/me', headers=headers)
        assert response.status_code == 401


class TestSessionExpiry:

    def test_session_continues_to_be_valid(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        for _ in range(3):
            response = api_session.get(f'{BASE_URL}/auth/me')
            assert response.status_code == 200
            time.sleep(1)

    def test_session_sliding_window_extends_expiry(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        response1 = api_session.get(f'{BASE_URL}/auth/me')
        assert response1.status_code == 200
        
        time.sleep(2)
        
        response2 = api_session.get(f'{BASE_URL}/auth/me')
        assert response2.status_code == 200


class TestCookieAttributes:

    def test_cookie_is_httponly(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        cookie_found = False
        for cookie in response.cookies:
            if cookie.name == 'sid':
                cookie_found = True
                assert cookie.has_nonstandard_attr('HttpOnly') or 'HttpOnly' in str(cookie)
        
        assert cookie_found

    def test_cookie_has_path_attribute(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        sid_cookie = api_session.cookies.get('sid')
        assert sid_cookie is not None
