import pytest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models import User


@pytest.fixture
def sample_user(client, app_context):
    from models import db
    user = User(
        username='testuser',
        email='testuser@example.com'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user

class TestLogin:
    def test_login_success(self, client, sample_user):
        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        response = client.post(
            '/api/login',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'token' in response_data

    def test_login_wrong_username(self, client, sample_user):
        data = {
            'username': 'wronguser',
            'password': 'password123'
        }
        response = client.post(
            '/api/login',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 401 
        response_data = json.loads(response.data)
        assert response_data['success'] is False

    def test_login_missing_fields(self, client):
        incomplete_data = {'username': 'testuser'}
        response = client.post(
            '/api/login',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False    
        assert 'Missing username or password' in response_data['message']
    
    def test_login_wrong_password(self, client, sample_user):
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = client.post(
            '/api/login',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Invalid credentials' in response_data['message']
        assert 'token' not in response_data

    def test_login_empty_body(self, client):
        response = client.post(
            '/api/login',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Missing username or password' in response_data['message']
        assert 'token' not in response_data
    
    def test_login_nonexistent_user(self, client):
        data = {
            'username': 'nonexistentuser',
            'password': 'password123'
        }
        response = client.post(
            '/api/login',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Invalid credentials' in response_data['message']
        assert 'token' not in response_data
    
    def test_login_invalid_json(self, client):
        response = client.post(
            '/api/login',
            data='invalid-json',
            content_type='application/json'
        )
        assert response.status_code == 500
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert 'Login failed' in response_data['message']
        assert 'token' not in response_data




