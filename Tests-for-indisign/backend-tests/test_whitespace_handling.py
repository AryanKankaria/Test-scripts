import pytest
import requests
import http.client
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')


class TestPasswordWhitespace:

    def test_login_password_leading_whitespace(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': f' {TEST_USER_PASSWORD}'}
        )
        assert response.status_code == 401

    def test_login_password_trailing_whitespace(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': f'{TEST_USER_PASSWORD} '}
        )
        assert response.status_code == 401

    def test_login_password_both_sides_whitespace(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': f' {TEST_USER_PASSWORD} '}
        )
        assert response.status_code == 401

    def test_login_password_tab_character(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': f'\t{TEST_USER_PASSWORD}'}
        )
        assert response.status_code == 401

    def test_login_password_newline_character(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': f'\n{TEST_USER_PASSWORD}'}
        )
        assert response.status_code == 401


class TestEmailWhitespaceVariations:

    def test_login_email_uppercase_with_whitespace(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': f' {TEST_USER_EMAIL.upper()} ', 'password': TEST_USER_PASSWORD}
        )
        # Email is trimmed and lowercased, so should match
        assert response.status_code == 200

    def test_login_email_mixed_case_with_trailing_whitespace(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': f'{TEST_USER_EMAIL.upper()} ', 'password': TEST_USER_PASSWORD}
        )
        # Email is trimmed and lowercased, so should match
        assert response.status_code == 200

    def test_login_email_tab_characters(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': f'\t{TEST_USER_EMAIL}\t', 'password': TEST_USER_PASSWORD}
        )
        # JavaScript .trim() removes tabs, so should match
        assert response.status_code == 200


class TestBearerTokenWhitespace:

    def test_bearer_token_leading_whitespace(self, api_session):
        """A leading space before 'Bearer' is OWS (RFC 7230 §3.2.3) and is stripped
        by the HTTP parser before reaching application code. The valid token is therefore
        extracted correctly and the request succeeds with 200."""
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login_response.status_code == 200
        token = api_session.cookies.get('sid')

        # Use http.client directly — requests rejects header values with leading spaces
        # (client-side RFC 7230 enforcement). http.client sends them as-is, but the
        # receiving server still strips OWS at the HTTP parsing layer.
        parsed = urlparse(BASE_URL)
        ConnClass = http.client.HTTPSConnection if parsed.scheme == 'https' else http.client.HTTPConnection
        conn = ConnClass(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80))
        conn.request('GET', '/auth/verify', headers={'Authorization': f' Bearer {token}'})
        response = conn.getresponse()
        conn.close()

        assert response.status == 200, (
            f"Expected 200: leading space is OWS and stripped by the HTTP layer, "
            f"so the token resolves normally. Got {response.status}"
        )
