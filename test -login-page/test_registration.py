import json
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models import User


@pytest.fixture
def sample_user(client, app_context):
    from models import db
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


class TestRegistration:
    def test_registration_success(self, client):
        response = client.post(
            '/api/register',
            data=json.dumps({
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'newpassword'
            }),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'User registered successfully' in data['message']
        assert data['user']['username'] == 'newuser'
        assert data['user']['email'] == 'newuser@example.com'

    def test_register_duplicate_username(self, client, sample_user):
        response = client.post(
            '/api/register',
            data=json.dumps({
                'username': 'testuser',
                'email': 'newuser@example.com',
                'password': 'newpassword'
            }),
            content_type='application/json'
        )
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Username already exists' in data['message']

    def test_register_duplicate_email(self, client, sample_user):
        response = client.post(
            '/api/register',
            data=json.dumps({
                'username': 'newuser',
                'email': 'test@example.com',
                'password': 'newpassword'
            }),
            content_type='application/json'
        )
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Email already registered' in data['message']

    def test_register_empty_body(self, client):
        response = client.post(
            '/api/register',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required fields' in data['message']

    def test_register_whitespace_username(self, client):
        response = client.post(
            '/api/register',
            data=json.dumps({
                'username': '   ',
                'email': 'newuser@example.com',
                'password': 'newpassword'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_register_short_password(self, client):
        response = client.post(
            '/api/register',
            data=json.dumps({
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'short'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'at least 6 characters' in data['message']

    def test_register_invalid_email(self, client):
        response = client.post(
            '/api/register',
            data=json.dumps({
                'username': 'newuser',
                'email': 'invalid-email',
                'password': 'newpassword'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid email format' in data['message']

    def test_register_short_username(self, client):
        response = client.post(
            '/api/register',
            data=json.dumps({
                'username': 'ab',
                'email': 'newuser@example.com',
                'password': 'newpassword'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'at least 3 characters' in data['message']
