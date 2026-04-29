import os
import sys
import json
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models import User
from jwt_utils import create_access_token, verify_token, decode_token


class TestJWTCreation:
    
    def test_token_creation(self):
        token = create_access_token(
            user_id='test-123',
            username='testuser',
            email='test@example.com'
        )
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_has_three_parts(self):
        token = create_access_token(
            user_id='test-123',
            username='testuser',
            email='test@example.com'
        )
        parts = token.split('.')
        assert len(parts) == 3  # header.payload.signature
    
    def test_token_contains_correct_claims(self):
        token = create_access_token(
            user_id='user-abc',
            username='john_doe',
            email='john@example.com'
        )
        
        payload = decode_token(token)
        assert payload is not None
        assert payload['sub'] == 'user-abc'  # 'sub' is the identity
        assert payload['username'] == 'john_doe'
        assert payload['email'] == 'john@example.com'
    
    def test_token_has_expiration(self):
        token = create_access_token(
            user_id='test-123',
            username='testuser',
            email='test@example.com'
        )
        
        payload = decode_token(token)
        assert 'exp' in payload
        assert 'iat' in payload
        # exp (expiration) should be after iat (issued at)
        assert payload['exp'] > payload['iat']
    
    def test_token_expiration_is_24_hours(self):
        token = create_access_token(
            user_id='test-123',
            username='testuser',
            email='test@example.com'
        )
        
        payload = decode_token(token)
        exp_time = datetime.fromtimestamp(payload['exp'])
        iat_time = datetime.fromtimestamp(payload['iat'])
        
        # Should be approximately 24 hours
        diff = exp_time - iat_time
        assert timedelta(hours=23, minutes=59) < diff < timedelta(hours=24, minutes=1)


class TestJWTVerification:
    
    def test_verify_valid_token(self):
        token = create_access_token(
            user_id='test-123',
            username='testuser',
            email='test@example.com'
        )
        
        payload = verify_token(token)
        assert payload is not None
        assert payload['sub'] == 'test-123'
    
    def test_verify_invalid_token(self):
        invalid_token = 'invalid.token.here'
        payload = verify_token(invalid_token)
        assert payload is None
    
    def test_verify_tampered_token(self):
        token = create_access_token(
            user_id='test-123',
            username='testuser',
            email='test@example.com'
        )
        
        # Tamper with token by changing last character
        tampered = token[:-1] + 'X'
        payload = verify_token(tampered)
        assert payload is None


class TestJWTWithLogin(object):
    
    def test_login_returns_token(self, client, app_context):
        from models import db
        
        # Create a user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Login
        response = client.post(
            '/api/login',
            data=json.dumps({
                'username': 'testuser',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'token' in data
        assert isinstance(data['token'], str)
    
    def test_token_from_login_is_valid(self, client, app_context):
        from models import db
        
        # Create a user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Login and get token
        response = client.post(
            '/api/login',
            data=json.dumps({
                'username': 'testuser',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        token = data['token']
        
        payload = verify_token(token)
        assert payload is not None
        assert payload['username'] == 'testuser'
        assert payload['email'] == 'test@example.com'
    
    def test_token_in_authorization_header(self, client, app_context):
        from models import db
        
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Login and get token
        response = client.post(
            '/api/login',
            data=json.dumps({
                'username': 'testuser',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        token = json.loads(response.data)['token']
        
        response = client.get(
            '/api/user/profile',
            headers={
                'Authorization': f'Bearer {token}'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['username'] == 'testuser'
    
    def test_request_without_token_fails(self, client):
        response = client.get('/api/user/profile')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Authorization' in data['message'] or 'token' in data['message'].lower()
    
    def test_invalid_token_fails(self, client):
        response = client.get(
            '/api/user/profile',
            headers={
                'Authorization': 'Bearer invalid.token.here'
            }
        )
        assert response.status_code == 401


class TestTokenVerificationEndpoint:
    
    def test_verify_endpoint_with_valid_token(self, client, app_context):
        from models import db
        
        # Create and login user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        response = client.post(
            '/api/login',
            data=json.dumps({
                'username': 'testuser',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        token = json.loads(response.data)['token']
        
        # Verify token via endpoint
        response = client.post(
            '/api/verify',
            data=json.dumps({'token': token}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['payload']['username'] == 'testuser'
    
    def test_verify_endpoint_with_invalid_token(self, client):
        response = client.post(
            '/api/verify',
            data=json.dumps({'token': 'invalid.token.here'}),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False