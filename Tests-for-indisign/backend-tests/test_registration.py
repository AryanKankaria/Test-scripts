import pytest
import requests
import os
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgres://postgres:1234@localhost:5432/indisign')

REG_TEST_EMAIL = 'reg_test@example.com'
REG_DUP_EMAIL = 'reg_dup_test@example.com'

VALID_PAYLOAD = {
    'first_name': 'Test',
    'last_name': 'Register',
    'email': REG_TEST_EMAIL,
    'phone_number': '9876543210',
    'password': 'RegPass@123',
}


def _db_conn():
    p = urlparse(DATABASE_URL)
    return psycopg2.connect(
        host=p.hostname or 'localhost',
        port=p.port or 5432,
        user=p.username or 'postgres',
        password=p.password or '1234',
        database=p.path.lstrip('/') or 'indisign',
    )


def _delete_pending(*emails):
    try:
        conn = _db_conn()
        cur = conn.cursor()
        for email in emails:
            cur.execute('DELETE FROM pending_users WHERE email = %s', (email,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f'[CLEANUP] pending_users cleanup error: {e}')



@pytest.fixture(autouse=True)
def cleanup_reg_emails():
    """Wipe both test emails from pending_users before and after every test."""
    _delete_pending(REG_TEST_EMAIL, REG_DUP_EMAIL)
    yield
    _delete_pending(REG_TEST_EMAIL, REG_DUP_EMAIL)



class TestRegistrationSuccess:

    def test_returns_201_with_pending_id(self, api_session):
        r = api_session.post(f'{BASE_URL}/users/new', json=VALID_PAYLOAD)
        assert r.status_code == 201
        data = r.json()
        assert 'pending_id' in data
        assert data['pending_id'] is not None

    def test_both_verification_flags_start_false(self, api_session):
        r = api_session.post(f'{BASE_URL}/users/new', json=VALID_PAYLOAD)
        assert r.status_code == 201
        data = r.json()
        assert data['phone_verified'] is False
        assert data['email_verified'] is False

    def test_response_includes_message(self, api_session):
        r = api_session.post(f'{BASE_URL}/users/new', json=VALID_PAYLOAD)
        assert r.status_code == 201
        assert 'message' in r.json()

    def test_accepts_valid_full_address(self, api_session):
        payload = {**VALID_PAYLOAD, 'address': {
            'pincode': '400001', 'area': 'Fort',
            'district': 'Mumbai', 'state': 'Maharashtra',
        }}
        r = api_session.post(f'{BASE_URL}/users/new', json=payload)
        assert r.status_code == 201

    def test_accepts_optional_middle_name_and_dob(self, api_session):
        payload = {**VALID_PAYLOAD, 'middle_name': 'Middle', 'dob': '2000-06-15'}
        r = api_session.post(f'{BASE_URL}/users/new', json=payload)
        assert r.status_code == 201




class TestRegistrationRequiredFields:

    def test_missing_email_returns_400(self, api_session):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'email'}
        assert api_session.post(f'{BASE_URL}/users/new', json=payload).status_code == 400

    def test_missing_password_returns_400(self, api_session):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'password'}
        assert api_session.post(f'{BASE_URL}/users/new', json=payload).status_code == 400

    def test_missing_first_name_returns_400(self, api_session):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'first_name'}
        assert api_session.post(f'{BASE_URL}/users/new', json=payload).status_code == 400

    def test_missing_last_name_returns_400(self, api_session):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'last_name'}
        assert api_session.post(f'{BASE_URL}/users/new', json=payload).status_code == 400

    def test_missing_phone_number_returns_400(self, api_session):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'phone_number'}
        assert api_session.post(f'{BASE_URL}/users/new', json=payload).status_code == 400

    def test_empty_body_returns_400(self, api_session):
        assert api_session.post(f'{BASE_URL}/users/new', json={}).status_code == 400

    def test_missing_fields_response_has_error_key(self, api_session):
        r = api_session.post(f'{BASE_URL}/users/new', json={'email': REG_TEST_EMAIL})
        assert r.status_code == 400
        assert 'error' in r.json()



class TestRegistrationAddressValidation:

    def test_address_missing_pincode_returns_400(self, api_session):
        payload = {**VALID_PAYLOAD, 'address': {
            'area': 'Fort', 'district': 'Mumbai', 'state': 'MH',
        }}
        assert api_session.post(f'{BASE_URL}/users/new', json=payload).status_code == 400

    def test_address_missing_area_returns_400(self, api_session):
        payload = {**VALID_PAYLOAD, 'address': {
            'pincode': '400001', 'district': 'Mumbai', 'state': 'MH',
        }}
        assert api_session.post(f'{BASE_URL}/users/new', json=payload).status_code == 400

    def test_address_missing_district_returns_400(self, api_session):
        payload = {**VALID_PAYLOAD, 'address': {
            'pincode': '400001', 'area': 'Fort', 'state': 'MH',
        }}
        assert api_session.post(f'{BASE_URL}/users/new', json=payload).status_code == 400

    def test_address_missing_state_returns_400(self, api_session):
        payload = {**VALID_PAYLOAD, 'address': {
            'pincode': '400001', 'area': 'Fort', 'district': 'Mumbai',
        }}
        assert api_session.post(f'{BASE_URL}/users/new', json=payload).status_code == 400

    def test_omitting_address_field_entirely_is_valid(self, api_session):
        """Address is optional — the whole field may be absent."""
        assert api_session.post(f'{BASE_URL}/users/new', json=VALID_PAYLOAD).status_code == 201




class TestRegistrationDuplicates:

    def test_email_already_in_users_table_returns_409(self, api_session):
        payload = {**VALID_PAYLOAD, 'email': TEST_USER_EMAIL}
        r = api_session.post(f'{BASE_URL}/users/new', json=payload)
        assert r.status_code == 409

    def test_email_conflict_error_mentions_email(self, api_session):
        payload = {**VALID_PAYLOAD, 'email': TEST_USER_EMAIL}
        r = api_session.post(f'{BASE_URL}/users/new', json=payload)
        assert 'email' in r.json()['error'].lower()

    def test_duplicate_pending_email_returns_409_with_same_pending_id(self, api_session):
        first = api_session.post(f'{BASE_URL}/users/new', json=VALID_PAYLOAD)
        second = api_session.post(f'{BASE_URL}/users/new', json=VALID_PAYLOAD)
        assert second.status_code == 409
        assert second.json().get('pending_id') == first.json()['pending_id']

    def test_duplicate_pending_email_includes_verification_flags(self, api_session):
        api_session.post(f'{BASE_URL}/users/new', json=VALID_PAYLOAD)
        r = api_session.post(f'{BASE_URL}/users/new', json=VALID_PAYLOAD)
        data = r.json()
        assert 'phone_verified' in data
        assert 'email_verified' in data

    def test_duplicate_phone_in_pending_returns_409(self, api_session):
        """Same phone_number already pending under a different email → 409."""
        api_session.post(f'{BASE_URL}/users/new', json=VALID_PAYLOAD)
        payload_diff_email = {**VALID_PAYLOAD, 'email': REG_DUP_EMAIL}
        r = api_session.post(f'{BASE_URL}/users/new', json=payload_diff_email)
        assert r.status_code == 409



class TestRegistrationExtremeInputs:

    def test_extremely_long_email_returns_json_not_crash(self, api_session):
        """302-char email exceeds VARCHAR(255) — server must return JSON, not hang."""
        long_email = 'a' * 290 + '@example.com'
        r = api_session.post(f'{BASE_URL}/users/new', json={**VALID_PAYLOAD, 'email': long_email})
        assert r.headers.get('content-type', '').startswith('application/json')

    def test_extremely_long_email_does_not_register(self, api_session):
        """302-char email must be rejected — DB VARCHAR(255) will not accept it."""
        long_email = 'a' * 290 + '@example.com'
        r = api_session.post(f'{BASE_URL}/users/new', json={**VALID_PAYLOAD, 'email': long_email})
        assert r.status_code in (400, 413, 422), (
            f'Expected 400/413/422 for an email exceeding 255 chars, got {r.status_code}'
        )

    def test_extremely_long_password_registers_successfully(self, api_session):
        """bcrypt silently truncates input at 72 bytes — /users/new has no max-length guard.
        A 500-char password therefore registers fine (first 72 bytes are hashed).
        """
        long_pw = 'Aa1@' * 125  # 500 chars, meets all complexity rules
        r = api_session.post(f'{BASE_URL}/users/new', json={**VALID_PAYLOAD, 'password': long_pw})
        assert r.status_code == 201

    def test_extremely_long_first_name_returns_json(self, api_session):
        """500-char first_name — server must return a JSON response, not crash."""
        r = api_session.post(
            f'{BASE_URL}/users/new',
            json={**VALID_PAYLOAD, 'first_name': 'A' * 500},
        )
        assert r.headers.get('content-type', '').startswith('application/json')

    def test_sql_injection_in_password_does_not_return_500(self, api_session):
        """SQL injection payload in password is bcrypt-hashed — parameterised queries are safe."""
        r = api_session.post(
            f'{BASE_URL}/users/new',
            json={**VALID_PAYLOAD, 'password': "'; DROP TABLE users; --"},
        )
        assert r.status_code in (201, 400, 409, 422), (
            f'Expected a controlled response for SQL injection input, got {r.status_code}'
        )

    def test_unicode_name_fields_do_not_crash_server(self, api_session):
        """UTF-8 multibyte characters in name fields must be handled gracefully."""
        r = api_session.post(
            f'{BASE_URL}/users/new',
            json={**VALID_PAYLOAD, 'first_name': '日本語', 'last_name': 'नाम'},
        )
        assert r.status_code != 500
