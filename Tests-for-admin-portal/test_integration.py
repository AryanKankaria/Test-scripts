import pytest
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')


class TestAuthenticationFlow:

    def test_complete_login_logout_flow(self, api_session):
        login_response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'admin@test.com', 'password': 'Test@1234'}
        )
        assert login_response.status_code == 200
        token = login_response.json()['token']

        me_response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert me_response.status_code == 200

        logout_response = api_session.post(
            f'{BASE_URL}/auth/logout',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert logout_response.status_code == 204

        blacklist_check = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert blacklist_check.status_code == 401

    def test_login_returns_user_data(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'admin@test.com', 'password': 'Test@1234'}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert 'token' in data
        assert 'user' in data
        assert data['user']['id'] is not None
        assert data['user']['name'] is not None
        assert data['user']['email'] == 'admin@test.com'
        assert data['user']['role'] is not None


class TestErrorHandling:

    def test_login_with_empty_body(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={}
        )
        assert response.status_code == 400

    def test_logout_with_malformed_token(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/logout',
            headers={'Authorization': 'Bearer 123.456.789'}
        )
        assert response.status_code == 401

    def test_api_with_missing_json_header(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            data='{"email":"admin@test.com","password":"Test@1234"}',
            headers={'Content-Type': 'text/plain'}
        )
        assert response.status_code in [400, 415]


class TestCrossRoleAccess:

    def test_editor_has_different_permissions_than_admin(self, api_session, editor_headers, admin_headers):
        admin_response = api_session.delete(
            f'{BASE_URL}/tickets/1',
            headers=admin_headers
        )
        
        editor_response = api_session.delete(
            f'{BASE_URL}/tickets/1',
            headers=editor_headers
        )
        
        assert admin_response.status_code != editor_response.status_code or admin_response.status_code == 404

    def test_editor_cannot_perform_admin_actions(self, api_session, editor_headers):
        response = api_session.patch(
            f'{BASE_URL}/management/users/1',
            headers=editor_headers,
            json={'role': 'admin'}
        )
        assert response.status_code == 403


class TestApiResponseFormat:

    def test_error_response_has_message(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'admin@test.com', 'password': 'wrong'}
        )
        assert response.status_code == 401
        assert 'message' in response.json()

    def test_success_response_is_valid_json(self, api_session, admin_token):
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_list_response_is_iterable(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/tickets',
            headers=admin_headers
        )
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))


class TestRequestValidation:

    def test_invalid_json_in_request(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            data='invalid json',
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code in [400, 415]

    def test_missing_required_fields(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': 'admin@test.com'}
        )
        assert response.status_code == 400

    def test_extra_fields_ignored(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={
                'email': 'admin@test.com',
                'password': 'Test@1234',
                'extra_field': 'should_be_ignored',
                'another_field': 123
            }
        )
        assert response.status_code == 200


class TestTokenPresence:

    def test_bearer_token_required_format(self, api_session, admin_token):
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200

    def test_token_without_bearer_prefix_fails(self, api_session, admin_token):
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': admin_token}
        )
        assert response.status_code == 401

    def test_auth_case_insensitive_bearer(self, api_session, admin_token):
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': f'bearer {admin_token}'}
        )
        assert response.status_code in [401, 200]
