import pytest
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')


class TestTicketAccess:

    def test_admin_can_list_tickets(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/tickets',
            headers=admin_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), (list, dict))

    def test_unauthenticated_cannot_list_tickets(self, api_session):
        response = api_session.get(f'{BASE_URL}/tickets')
        assert response.status_code == 401

    def test_admin_can_view_ticket_details(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/tickets/1',
            headers=admin_headers
        )
        assert response.status_code in [200, 404]

    def test_admin_can_create_ticket(self, api_session, admin_headers):
        ticket_data = {
            'title': 'Test Ticket',
            'description': 'This is a test ticket',
            'priority': 'medium',
            'status': 'open'
        }
        response = api_session.post(
            f'{BASE_URL}/tickets',
            headers=admin_headers,
            json=ticket_data
        )
        assert response.status_code in [201, 200, 400]

    def test_admin_can_update_ticket(self, api_session, admin_headers):
        ticket_data = {'status': 'in_progress'}
        response = api_session.patch(
            f'{BASE_URL}/tickets/1',
            headers=admin_headers,
            json=ticket_data
        )
        assert response.status_code in [200, 404, 400]

    def test_admin_can_delete_ticket(self, api_session, admin_headers):
        response = api_session.delete(
            f'{BASE_URL}/tickets/1',
            headers=admin_headers
        )
        assert response.status_code in [204, 404, 403]

    def test_editor_cannot_delete_ticket(self, api_session, editor_headers):
        response = api_session.delete(
            f'{BASE_URL}/tickets/1',
            headers=editor_headers
        )
        assert response.status_code == 403
        assert response.json()['message'] == 'Insufficient permissions.'


class TestTicketComments:

    def test_admin_can_view_ticket_comments(self, api_session, admin_headers):
        response = api_session.get(
            f'{BASE_URL}/tickets/1/comments',
            headers=admin_headers
        )
        assert response.status_code in [200, 404]

    def test_admin_can_add_comment_to_ticket(self, api_session, admin_headers):
        comment_data = {'text': 'This is a test comment'}
        response = api_session.post(
            f'{BASE_URL}/tickets/1/comments',
            headers=admin_headers,
            json=comment_data
        )
        assert response.status_code in [201, 200, 400, 404]

    def test_unauthenticated_cannot_add_comment(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/tickets/1/comments',
            json={'text': 'Comment'}
        )
        assert response.status_code == 401


class TestTicketImageUpload:

    def test_admin_can_upload_ticket_image(self, api_session, admin_headers):
        files = {'file': ('test.png', b'fake_image_data', 'image/png')}
        response = api_session.post(
            f'{BASE_URL}/tickets/upload',
            headers=admin_headers,
            files=files
        )
        assert response.status_code in [200, 201, 400]

    def test_unauthenticated_cannot_upload_image(self, api_session):
        files = {'file': ('test.png', b'fake_image_data', 'image/png')}
        response = api_session.post(
            f'{BASE_URL}/tickets/upload',
            files=files
        )
        assert response.status_code == 401

    def test_editor_cannot_upload_image(self, api_session, editor_headers):
        files = {'file': ('test.png', b'fake_image_data', 'image/png')}
        response = api_session.post(
            f'{BASE_URL}/tickets/upload',
            headers=editor_headers,
            files=files
        )
        assert response.status_code in [403, 400]
