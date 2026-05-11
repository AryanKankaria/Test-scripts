import pytest
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')

VALIDATE_URL = f'{BASE_URL}/api/v1/password/validate'

# Allowed special characters per the backend implementation
ALLOWED_SPECIALS = '!@#$%^&*_-+=?.'





class TestPasswordValidationValid:

    def test_strong_password_is_valid(self, api_session):
        r = api_session.post(VALIDATE_URL, json={'password': 'StrongP@ss1'})
        assert r.status_code == 200
        data = r.json()
        for field in ('valid', 'strength', 'score', 'errors', 'suggestions'):
            assert field in data, f"Response missing field: {field}"
        assert data['valid'] is True
        assert data['strength'] in ('strong', 'very_strong')
        assert data['score'] >= 4
        assert data['errors'] == []



class TestPasswordLength:

    def test_7_char_password_triggers_too_short(self, api_session):
        r = api_session.post(VALIDATE_URL, json={'password': 'Ab1@xyz'})  # 7 chars
        assert r.status_code == 200
        assert 'PASSWORD_TOO_SHORT' in r.json()['errors']

    def test_129_char_password_triggers_too_long(self, api_session):
        pw = 'Aa1@' * 33  # 132 chars — over the 128-char limit
        r = api_session.post(VALIDATE_URL, json={'password': pw})
        assert r.status_code == 200
        assert 'PASSWORD_TOO_LONG' in r.json()['errors']



class TestPasswordComplexityErrors:

    def test_no_lowercase_flagged(self, api_session):
        r = api_session.post(VALIDATE_URL, json={'password': 'NOLOWER1@'})
        assert 'PASSWORD_NO_LOWERCASE' in r.json()['errors']

    def test_no_uppercase_flagged(self, api_session):
        r = api_session.post(VALIDATE_URL, json={'password': 'noupper1@'})
        assert 'PASSWORD_NO_UPPERCASE' in r.json()['errors']

    def test_no_digit_flagged(self, api_session):
        r = api_session.post(VALIDATE_URL, json={'password': 'NoDigit@!'})
        assert 'PASSWORD_NO_DIGIT' in r.json()['errors']

    def test_no_special_char_flagged(self, api_session):
        r = api_session.post(VALIDATE_URL, json={'password': 'NoSpecial1'})
        assert 'PASSWORD_NO_SPECIAL' in r.json()['errors']

    def test_disallowed_char_space_flagged(self, api_session):
        """Space is not in the allowed special-character set."""
        r = api_session.post(VALIDATE_URL, json={'password': 'Invalid Pass1@'})
        assert 'PASSWORD_INVALID_CHARS' in r.json()['errors']



class TestPasswordCommonAndMissing:

    def test_common_password_flagged(self, api_session):
        r = api_session.post(VALIDATE_URL, json={'password': 'password123'})
        assert r.status_code == 200
        assert 'PASSWORD_COMMON' in r.json()['errors']
        assert r.json()['valid'] is False

    def test_missing_password_field_returns_400(self, api_session):
        r = api_session.post(VALIDATE_URL, json={})
        assert r.status_code == 400
