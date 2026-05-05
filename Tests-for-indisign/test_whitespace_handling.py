import pytest
import requests
import os
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

    def test_bearer_token_extra_spaces_before_token(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login_response.status_code == 200
        token = api_session.cookies.get('sid')
        
        new_session = requests.Session()
        headers = {'Authorization': f'Bearer  {token}'}
        response = new_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        # Backend removes anything before the token, so should still work
        assert response.status_code == 200

    def test_bearer_token_leading_whitespace(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert login_response.status_code == 200
        token = api_session.cookies.get('sid')

        new_session = requests.Session()
        # Leading whitespace in header values is forbidden by RFC 7230.
        # requests enforces this client-side, so the backend never receives this.
        with pytest.raises(requests.exceptions.InvalidHeader):
            new_session.get(
                f'{BASE_URL}/auth/verify',
                headers={'Authorization': f' Bearer {token}'}
            )
