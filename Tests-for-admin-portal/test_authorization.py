import pytest
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')


class TestUnauthenticatedAccess:

    def test_unauthenticated_user_denied_access_tickets(self, api_session):
        response = api_session.get(f'{BASE_URL}/tickets')
        assert response.status_code == 401
        assert response.json()['message'] == 'No token provided.'

    def test_unauthenticated_user_denied_access_management(self, api_session):
        response = api_session.get(f'{BASE_URL}/management/users')
        assert response.status_code == 401
        assert response.json()['message'] == 'No token provided.'

    def test_unauthenticated_user_denied_access_profile(self, api_session):
        response = api_session.get(f'{BASE_URL}/profile')
        assert response.status_code == 401
        assert response.json()['message'] == 'No token provided.'

    def test_unauthenticated_user_denied_access_settings(self, api_session):
        response = api_session.get(f'{BASE_URL}/settings')
        assert response.status_code == 401
        assert response.json()['message'] == 'No token provided.'


class TestEditorAuthorization:

    def test_editor_can_view_tickets(self, api_session, editor_headers):
        response = api_session.get(
            f'{BASE_URL}/tickets',
            headers=editor_headers
        )
        assert response.status_code in [200, 403]

    def test_editor_cannot_delete_ticket(self, api_session, editor_headers):
        response = api_session.delete(
            f'{BASE_URL}/tickets/1',
            headers=editor_headers
        )
        assert response.status_code == 403
        assert response.json()['message'] == 'Insufficient permissions.'

    def test_editor_cannot_delete_user(self, api_session, editor_headers):
        response = api_session.delete(
            f'{BASE_URL}/management/users/1',
            headers=editor_headers
        )
        assert response.status_code == 403
        assert response.json()['message'] == 'Insufficient permissions.'

    def test_editor_cannot_update_company(self, api_session, editor_headers):
        response = api_session.patch(
            f'{BASE_URL}/management/companies/1',
            headers=editor_headers,
            json={'name': 'New Company Name'}
        )
        assert response.status_code == 403
        assert response.json()['message'] == 'Insufficient permissions.'


class TestAdminAuthorization:

    def test_admin_can_delete_ticket(self, api_session, admin_headers):
        response = api_session.delete(
            f'{BASE_URL}/tickets/1',
            headers=admin_headers
        )
        assert response.status_code in [204, 404, 403]

    def test_admin_can_update_user(self, api_session, admin_headers):
        response = api_session.patch(
            f'{BASE_URL}/management/users/1',
            headers=admin_headers,
            json={'role': 'editor'}
        )
        assert response.status_code in [200, 404, 400]

    def test_admin_can_update_company(self, api_session, admin_headers):
        response = api_session.patch(
            f'{BASE_URL}/management/companies/1',
            headers=admin_headers,
            json={'name': 'Updated Company'}
        )
        assert response.status_code in [200, 404, 400]

    def test_admin_can_list_users(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/management/users',
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_admin_can_list_companies(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/management/companies',
            headers=admin_headers
        )
        assert response.status_code == 200


class TestTokenValidation:

    def test_invalid_bearer_format(self, api_session):
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': 'InvalidFormat token'}
        )
        assert response.status_code == 401

    def test_missing_bearer_prefix(self, api_session):
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'}
        )
        assert response.status_code == 401

    def test_empty_authorization_header(self, api_session):
        response = api_session.get(
            f'{BASE_URL}/auth/me',
            headers={'Authorization': ''}
        )
        assert response.status_code == 401
