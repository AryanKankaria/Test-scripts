import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')

FORGOT_URL = f'{BASE_URL}/auth/forgot-password'
RESET_URL = f'{BASE_URL}/auth/reset-password'

# A wrong OTP value used to trigger failure paths.
WRONG_OTP = '000000'

# Payload template for reset-password (OTP will always be wrong in these tests)
def _reset_payload(otp=WRONG_OTP, pw='NewPass@123'):
    return {
        'email': TEST_USER_EMAIL,
        'otp': otp,
        'new_password': pw,
        'confirm_password': pw,
    }



class TestForgotPassword:

    def test_valid_email_returns_200(self, api_session):
        r = api_session.post(FORGOT_URL, json={'email': TEST_USER_EMAIL})
        assert r.status_code == 200

    def test_valid_email_response_has_ok_true(self, api_session):
        r = api_session.post(FORGOT_URL, json={'email': TEST_USER_EMAIL})
        assert r.json().get('ok') is True

    def test_valid_email_response_includes_expires_in_minutes(self, api_session):
        r = api_session.post(FORGOT_URL, json={'email': TEST_USER_EMAIL})
        assert 'expires_in_minutes' in r.json()

    def test_nonexistent_email_also_returns_200(self, api_session):
        """Non-existent email must return 200 to prevent email enumeration."""
        r = api_session.post(FORGOT_URL, json={'email': 'no_such_user_xyz@example.com'})
        assert r.status_code == 200

    def test_nonexistent_email_response_has_ok_true(self, api_session):
        r = api_session.post(FORGOT_URL, json={'email': 'no_such_user_xyz@example.com'})
        assert r.json().get('ok') is True

    def test_missing_email_returns_400(self, api_session):
        r = api_session.post(FORGOT_URL, json={})
        assert r.status_code == 400

    def test_missing_email_response_has_error_key(self, api_session):
        r = api_session.post(FORGOT_URL, json={})
        assert 'error' in r.json()


class TestResetPasswordFieldValidation:

    def test_missing_email_returns_400(self, api_session):
        payload = {
            'otp': WRONG_OTP, 'new_password': 'NewPass@123', 'confirm_password': 'NewPass@123',
        }
        assert api_session.post(RESET_URL, json=payload).status_code == 400

    def test_missing_otp_returns_400(self, api_session):
        payload = {
            'email': TEST_USER_EMAIL, 'new_password': 'NewPass@123', 'confirm_password': 'NewPass@123',
        }
        assert api_session.post(RESET_URL, json=payload).status_code == 400

    def test_missing_new_password_returns_400(self, api_session):
        payload = {
            'email': TEST_USER_EMAIL, 'otp': WRONG_OTP, 'confirm_password': 'NewPass@123',
        }
        assert api_session.post(RESET_URL, json=payload).status_code == 400

    def test_missing_confirm_password_returns_400(self, api_session):
        payload = {
            'email': TEST_USER_EMAIL, 'otp': WRONG_OTP, 'new_password': 'NewPass@123',
        }
        assert api_session.post(RESET_URL, json=payload).status_code == 400

    def test_password_shorter_than_8_chars_returns_400(self, api_session):
        r = api_session.post(RESET_URL, json=_reset_payload(pw='Short1@'))
        assert r.status_code == 400

    def test_short_password_error_mentions_length(self, api_session):
        r = api_session.post(RESET_URL, json=_reset_payload(pw='Short1@'))
        assert '8' in r.json().get('error', '')

    def test_mismatched_passwords_return_400(self, api_session):
        payload = {
            'email': TEST_USER_EMAIL,
            'otp': WRONG_OTP,
            'new_password': 'NewPass@123',
            'confirm_password': 'Different@456',
        }
        r = api_session.post(RESET_URL, json=payload)
        assert r.status_code == 400

    def test_mismatched_passwords_error_mentions_match(self, api_session):
        payload = {
            'email': TEST_USER_EMAIL,
            'otp': WRONG_OTP,
            'new_password': 'NewPass@123',
            'confirm_password': 'Different@456',
        }
        r = api_session.post(RESET_URL, json=payload)
        assert 'match' in r.json().get('error', '').lower()


class TestResetPasswordNoOTP:

    def test_no_pending_otp_returns_400(self, api_session):
        """Calling reset-password without a prior forgot-password should fail."""
        r = api_session.post(RESET_URL, json=_reset_payload())
        assert r.status_code == 400

    def test_no_pending_otp_error_message(self, api_session):
        r = api_session.post(RESET_URL, json=_reset_payload())
        error = r.json().get('error', '').lower()
        assert 'no password reset' in error or 'request' in error or 'otp' in error


class TestResetPasswordWrongOTP:
    """
    These tests call forgot-password first to plant an in-memory OTP entry,
    then send a deliberately wrong OTP to exercise the failure paths.

    Progressive server-side delays apply:
      1st wrong OTP → 1 s wait before response
      2nd wrong OTP → 2 s wait before response
    Tests that go beyond 2 attempts are marked slow.

    NOTE: A successful reset cannot be integration-tested here because the
    real OTP lives only in the Node.js process memory and is never persisted
    to the database.  To enable a happy-path test, add a dev-only route that
    returns the pending OTP for a given email (e.g. GET /auth/_test/otp/:email).
    """

    def test_wrong_otp_returns_400(self, api_session):
        api_session.post(FORGOT_URL, json={'email': TEST_USER_EMAIL})
        r = api_session.post(RESET_URL, json=_reset_payload())
        assert r.status_code == 400

    def test_wrong_otp_error_says_invalid(self, api_session):
        api_session.post(FORGOT_URL, json={'email': TEST_USER_EMAIL})
        r = api_session.post(RESET_URL, json=_reset_payload())
        assert 'invalid otp' in r.json().get('error', '').lower()

    def test_wrong_otp_response_includes_attempts_remaining(self, api_session):
        api_session.post(FORGOT_URL, json={'email': TEST_USER_EMAIL})
        r = api_session.post(RESET_URL, json=_reset_payload())
        data = r.json()
        assert 'attempts_remaining' in data
        assert data['attempts_remaining'] == 4, (
            f"Expected 4 attempts remaining after first wrong OTP, got {data['attempts_remaining']}"
        )

    def test_attempts_remaining_decrements_on_each_failure(self, api_session):
        """Two consecutive wrong OTPs → attempts_remaining drops from 4 to 3.
        Total server-side delay: 1 s + 2 s = 3 s.
        """
        api_session.post(FORGOT_URL, json={'email': TEST_USER_EMAIL})
        r1 = api_session.post(RESET_URL, json=_reset_payload())
        r2 = api_session.post(RESET_URL, json=_reset_payload())
        assert r1.json().get('attempts_remaining') == 4
        assert r2.json().get('attempts_remaining') == 3

    @pytest.mark.slow
    def test_max_attempts_exceeded_returns_429(self, api_session):
        """After 5 wrong OTPs the endpoint returns 429 and deletes the OTP entry.
        Server-side delays: 1+2+4+8+16+16 = ~47 s total — run with -m slow only.
        """
        api_session.post(FORGOT_URL, json={'email': TEST_USER_EMAIL})
        for _ in range(5):
            api_session.post(RESET_URL, json=_reset_payload())
        r = api_session.post(RESET_URL, json=_reset_payload())
        assert r.status_code == 429

    @pytest.mark.slow
    def test_after_lockout_otp_entry_is_deleted(self, api_session):
        """After lockout (429), the OTP is erased — a fresh request must return
        'no password reset' rather than 'too many attempts'.
        Total wait: ~47 s — run with -m slow only.
        """
        api_session.post(FORGOT_URL, json={'email': TEST_USER_EMAIL})
        for _ in range(6):
            api_session.post(RESET_URL, json=_reset_payload())
        # OTP entry deleted; next call should return "no pending reset", not "too many attempts"
        r = api_session.post(RESET_URL, json=_reset_payload())
        assert r.status_code == 400, (
            f"Expected 400 (no pending OTP) after lockout clears entry, got {r.status_code}"
        )
        assert 'no password reset' in r.json().get('error', '').lower(), (
            f"Expected 'no password reset' error after OTP deletion, got: {r.json().get('error')}"
        )


# POST /auth/reset-password — session invalidation after successful reset

class TestResetPasswordSessionInvalidation:
    """
    Full happy-path test: call forgot-password, use the real OTP to reset the
    password, verify all prior sessions are invalidated.

    SKIPPED because the OTP is stored only in the Node.js process memory and
    is not exposed via any API or database column.

    To unskip: add a dev-only endpoint such as
        GET /auth/_test/pending-otp?email=<email>
    that returns the current OTP (gated by NODE_ENV !== 'production').
    """

    @pytest.mark.skip(reason=(
        'OTP is not accessible to these tests as I am not on UAT or prod. '
    ))
    def test_successful_reset_invalidates_existing_sessions(self, api_session):
        # 1. Log in to create a session
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD},
        )
        old_sid = api_session.cookies.get('sid')

        # 2. Request OTP and retrieve
        api_session.post(FORGOT_URL, json={'email': TEST_USER_EMAIL})
        real_otp = '<obtained from dev helper endpoint>'

        # 3. Reset password
        r = api_session.post(RESET_URL, json={
            'email': TEST_USER_EMAIL,
            'otp': real_otp,
            'new_password': TEST_USER_PASSWORD,
            'confirm_password': TEST_USER_PASSWORD,
        })
        assert r.status_code == 200
        assert r.json().get('ok') is True

        # 4. Old session must be invalidated
        old_session = requests.Session()
        old_session.cookies.set('sid', old_sid)
        verify = old_session.get(f'{BASE_URL}/auth/verify')
        assert verify.status_code == 401
