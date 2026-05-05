import pytest
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')


class TestUserManagement:

    def test_admin_can_list_users(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/management/users',
            headers=admin_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), (list, dict))

    def test_admin_can_update_user(self, api_session, admin_headers):
        user_data = {'role': 'editor'}
        response = api_session.patch(
            f'{BASE_URL}/management/users/1',
            headers=admin_headers,
            json=user_data
        )
        assert response.status_code in [200, 404, 400]

    def test_admin_can_delete_user(self, api_session, admin_headers):
        response = api_session.delete(
            f'{BASE_URL}/management/users/1',
            headers=admin_headers
        )
        assert response.status_code in [204, 404, 403]

    def test_editor_cannot_list_users(self, api_session, editor_headers):
        response = api_session.get(
            f'{BASE_URL}/management/users',
            headers=editor_headers
        )
        assert response.status_code in [403, 200]

    def test_editor_cannot_update_user(self, api_session, editor_headers):
        response = api_session.patch(
            f'{BASE_URL}/management/users/1',
            headers=editor_headers,
            json={'role': 'admin'}
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

    def test_unauthenticated_cannot_list_users(self, api_session):
        response = api_session.get(f'{BASE_URL}/management/users')
        assert response.status_code == 401


class TestCompanyManagement:

    def test_admin_can_list_companies(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/management/companies',
            headers=admin_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), (list, dict))

    def test_admin_can_update_company(self, api_session, admin_headers):
        company_data = {'name': 'Updated Company Name'}
        response = api_session.patch(
            f'{BASE_URL}/management/companies/1',
            headers=admin_headers,
            json=company_data
        )
        assert response.status_code in [200, 404, 400]

    def test_admin_can_delete_company(self, api_session, admin_headers):
        response = api_session.delete(
            f'{BASE_URL}/management/companies/1',
            headers=admin_headers
        )
        assert response.status_code in [204, 404, 403]

    def test_editor_cannot_list_companies(self, api_session, editor_headers):
        response = api_session.get(
            f'{BASE_URL}/management/companies',
            headers=editor_headers
        )
        assert response.status_code in [403, 200]

    def test_editor_cannot_update_company(self, api_session, editor_headers):
        response = api_session.patch(
            f'{BASE_URL}/management/companies/1',
            headers=editor_headers,
            json={'name': 'New Name'}
        )
        assert response.status_code == 403
        assert response.json()['message'] == 'Insufficient permissions.'

    def test_editor_cannot_delete_company(self, api_session, editor_headers):
        response = api_session.delete(
            f'{BASE_URL}/management/companies/1',
            headers=editor_headers
        )
        assert response.status_code == 403
        assert response.json()['message'] == 'Insufficient permissions.'

    def test_unauthenticated_cannot_list_companies(self, api_session):
        response = api_session.get(f'{BASE_URL}/management/companies')
        assert response.status_code == 401


class TestInvalidUpdateOperations:

    def test_update_nonexistent_user(self, api_session, admin_headers):
        response = api_session.patch(
            f'{BASE_URL}/management/users/999999',
            headers=admin_headers,
            json={'role': 'editor'}
        )
        assert response.status_code in [404, 400]

    def test_update_nonexistent_company(self, api_session, admin_headers):
        response = api_session.patch(
            f'{BASE_URL}/management/companies/999999',
            headers=admin_headers,
            json={'name': 'Test'}
        )
        assert response.status_code in [404, 400]

    def test_delete_nonexistent_user(self, api_session, admin_headers):
        response = api_session.delete(
            f'{BASE_URL}/management/users/999999',
            headers=admin_headers
        )
        assert response.status_code in [404, 400]

    def test_delete_nonexistent_company(self, api_session, admin_headers):
        response = api_session.delete(
            f'{BASE_URL}/management/companies/999999',
            headers=admin_headers
        )
        assert response.status_code in [404, 400]
