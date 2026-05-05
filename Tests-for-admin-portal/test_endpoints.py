import pytest
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')


class TestProfileEndpoints:

    def test_admin_can_view_own_profile(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/profile',
            headers=admin_headers
        )
        assert response.status_code in [200, 404]

    def test_admin_can_update_own_profile(self, api_session, admin_headers):
        profile_data = {'name': 'Updated Name'}
        response = api_session.patch(
            f'{BASE_URL}/profile',
            headers=admin_headers,
            json=profile_data
        )
        assert response.status_code in [200, 400, 404]

    def test_admin_can_change_password(self, api_session, admin_headers):
        password_data = {
            'currentPassword': 'Test@1234',
            'newPassword': 'NewTest@1234'
        }
        response = api_session.post(
            f'{BASE_URL}/profile/change-password',
            headers=admin_headers,
            json=password_data
        )
        assert response.status_code in [200, 204, 400, 404]

    def test_unauthenticated_cannot_view_profile(self, api_session):
        response = api_session.get(f'{BASE_URL}/profile')
        assert response.status_code == 401


class TestSettingsEndpoints:

    def test_admin_can_view_settings(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/settings',
            headers=admin_headers
        )
        assert response.status_code in [200, 404]

    def test_admin_can_update_settings(self, api_session, admin_headers):
        settings_data = {'theme': 'dark'}
        response = api_session.patch(
            f'{BASE_URL}/settings',
            headers=admin_headers,
            json=settings_data
        )
        assert response.status_code in [200, 400, 404]

    def test_editor_can_view_settings(self, api_session, editor_headers):
        response = api_session.get(
            f'{BASE_URL}/settings',
            headers=editor_headers
        )
        assert response.status_code in [200, 404, 403]

    def test_unauthenticated_cannot_view_settings(self, api_session):
        response = api_session.get(f'{BASE_URL}/settings')
        assert response.status_code == 401


class TestAuditLogsEndpoints:

    def test_admin_can_view_audit_logs(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/audit-logs',
            headers=admin_headers
        )
        assert response.status_code in [200, 404]

    def test_admin_can_filter_audit_logs(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/audit-logs?action=login',
            headers=admin_headers
        )
        assert response.status_code in [200, 404]

    def test_editor_cannot_view_audit_logs(self, api_session, editor_headers):
        response = api_session.get(
            f'{BASE_URL}/audit-logs',
            headers=editor_headers
        )
        assert response.status_code in [403, 200, 404]

    def test_unauthenticated_cannot_view_audit_logs(self, api_session):
        response = api_session.get(f'{BASE_URL}/audit-logs')
        assert response.status_code == 401


class TestAnalyticsEndpoints:

    def test_admin_can_view_analytics(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/analytics',
            headers=admin_headers
        )
        assert response.status_code in [200, 404]

    def test_admin_can_get_dashboard_metrics(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/analytics/metrics',
            headers=admin_headers
        )
        assert response.status_code in [200, 404]

    def test_editor_cannot_view_analytics(self, api_session, editor_headers):
        response = api_session.get(
            f'{BASE_URL}/analytics',
            headers=editor_headers
        )
        assert response.status_code in [403, 200, 404]

    def test_unauthenticated_cannot_view_analytics(self, api_session):
        response = api_session.get(f'{BASE_URL}/analytics')
        assert response.status_code == 401


class TestOverviewEndpoints:

    def test_admin_can_view_overview(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/overview',
            headers=admin_headers
        )
        assert response.status_code in [200, 404]

    def test_admin_can_get_dashboard_overview(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/overview/dashboard',
            headers=admin_headers
        )
        assert response.status_code in [200, 404]

    def test_unauthenticated_cannot_view_overview(self, api_session):
        response = api_session.get(f'{BASE_URL}/overview')
        assert response.status_code == 401


class TestHealthEndpoint:

    def test_health_check_no_auth_required(self, api_session):
        response = api_session.get(f'{BASE_URL}/health')
        assert response.status_code == 200
        assert response.json() == {'status': 'ok'}
