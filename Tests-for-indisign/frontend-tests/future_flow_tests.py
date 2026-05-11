"""
Full end-to-end flow tests for the indisign login/auth UI.

INTENDED USE
------------
These tests are designed to run against a pre-populated database — either prod or UAT.
Do NOT run them against an empty/fresh DB. Supply real account credentials via the
.env file (or environment variables) before running:

    TEST_USER_EMAIL      — a fully verified, active account
    TEST_USER_PASSWORD   — its password
    PENDING_USER_EMAIL   — an account that exists in pending_users (not yet verified)
    PENDING_USER_PASSWORD — its password
    APP_URL              — base URL of the frontend (default: http://localhost:4200)
    DATABASE_URL         — Postgres connection string; leave unset on prod/UAT to skip
                           DB-side teardown (the flows self-clean via logout instead)

RUN ONLY FLOW TESTS
-------------------
    pytest frontend-tests/future_flow_tests.py -v -m flow

EXCLUDE FROM UNIT RUNS
----------------------
    pytest frontend-tests/ -m "not flow" -v

DB CLEANLINESS
--------------
Every flow that creates a session ends with a logout (which deletes the session server-side).
The `cleanup_flow_sessions` fixture runs once after all tests finish and removes any leftover
sessions, cooldowns, and otp attempt counts for the configured test emails — falling back
silently if DATABASE_URL is not accessible (prod/UAT without direct DB access).
"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import Page, expect

load_dotenv(Path(__file__).parent.parent / '.env')

APP_URL               = os.getenv('APP_URL',               'http://localhost:4200')
DATABASE_URL          = os.getenv('DATABASE_URL',          '')
TEST_USER_EMAIL       = os.getenv('TEST_USER_EMAIL',       'testuser@example.com')
TEST_USER_PASSWORD    = os.getenv('TEST_USER_PASSWORD',    'TestPassword@123')
PENDING_USER_EMAIL    = os.getenv('PENDING_USER_EMAIL',    'pending@example.com')
PENDING_USER_PASSWORD = os.getenv('PENDING_USER_PASSWORD', 'PendingPass@123')

LOGIN_URL = f'{APP_URL}/login'

# Helpers

def _do_login(page: Page):
    """Navigate to login and sign in as the test user. Returns after dashboard loads."""
    page.goto(LOGIN_URL)
    page.locator('#email').fill(TEST_USER_EMAIL)
    page.locator('#password').fill(TEST_USER_PASSWORD)
    page.get_by_role('button', name='Sign In').click()
    page.wait_for_url(f'{APP_URL}/dashboard**', timeout=12_000)


def _do_logout(page: Page):
    """Click the logout control on the dashboard. Waits for redirect to /login.
    Update the locator below to match the actual logout button/link in the frontend."""
    # Common selectors — the first one that exists wins
    for selector in [
        '[data-testid="logout"]',
        'button:has-text("Logout")',
        'button:has-text("Sign out")',
        'a:has-text("Logout")',
        'a:has-text("Sign out")',
    ]:
        if page.locator(selector).count() > 0:
            page.locator(selector).first.click()
            page.wait_for_url(f'{APP_URL}/login**', timeout=8_000)
            return
    raise AssertionError(
        "Could not find a logout button. "
        "Update the selectors in _do_logout() to match the frontend."
    )


def _db_cleanup():
    """Remove leftover sessions, cooldowns, and OTP attempt counts for test emails.
    Silently skips if DATABASE_URL is not set or the DB is unreachable."""
    if not DATABASE_URL:
        return
    try:
        import psycopg2
        from urllib.parse import urlparse
        parsed = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 5432,
            user=parsed.username or 'postgres',
            password=parsed.password or '1234',
            database=parsed.path.lstrip('/') or 'indisign',
        )
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM sessions WHERE user_id IN "
            "(SELECT id FROM users WHERE email IN (%s, %s))",
            (TEST_USER_EMAIL, PENDING_USER_EMAIL)
        )
        cursor.execute("DELETE FROM login_cooldowns")
        cursor.execute(
            "DELETE FROM platform_logs WHERE action = 'login_failed' "
            "AND metadata->>'email' IN (%s, %s) "
            "AND created_at > NOW() - INTERVAL '1 hour'",
            (TEST_USER_EMAIL, PENDING_USER_EMAIL)
        )
        cursor.execute(
            "UPDATE pending_users SET otp_phone_attempts = 0, otp_email_attempts = 0 "
            "WHERE email = %s",
            (PENDING_USER_EMAIL,)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[WARNING] flow_test DB cleanup failed (non-fatal): {e}")


# Fixtures

@pytest.fixture(scope='session', autouse=True)
def cleanup_flow_sessions():
    """Session-scoped teardown: clean up any DB state left by flow tests."""
    yield
    _db_cleanup()


# FlowLoginLogout

@pytest.mark.flow
class FlowLoginLogout:
    """Full login → dashboard → logout cycle."""

    def test_login_redirects_to_dashboard(self, page: Page):
        _do_login(page)
        assert '/dashboard' in page.url

    def test_logout_redirects_to_login(self, page: Page):
        _do_login(page)
        _do_logout(page)
        assert '/login' in page.url

    def test_sid_cookie_absent_after_logout(self, page: Page):
        _do_login(page)
        _do_logout(page)
        cookie_names = [c['name'] for c in page.context.cookies()]
        assert 'sid' not in cookie_names

    def test_old_session_rejected_after_logout(self, page: Page):
        """A session token captured before logout must be rejected after logout."""
        _do_login(page)
        old_sid = next(
            (c['value'] for c in page.context.cookies() if c['name'] == 'sid'), None
        )
        assert old_sid, "sid cookie not found after login"
        _do_logout(page)

        # Re-inject the old token and attempt to reach a protected route
        page.context.add_cookies([{
            'name': 'sid',
            'value': old_sid,
            'domain': page.url.split('/')[2].split(':')[0],
            'path': '/',
        }])
        page.goto(f'{APP_URL}/dashboard')
        page.wait_for_url(f'{APP_URL}/login**', timeout=8_000)
        assert '/login' in page.url


# FlowProtectedRouteAccess

@pytest.mark.flow
class FlowProtectedRouteAccess:
    """Authenticated users can reach protected pages; unauthenticated users cannot."""

    def test_dashboard_accessible_when_logged_in(self, page: Page):
        _do_login(page)
        page.goto(f'{APP_URL}/dashboard')
        assert '/dashboard' in page.url

    def test_dashboard_redirects_unauthenticated(self, page: Page):
        page.goto(f'{APP_URL}/dashboard')
        page.wait_for_url(f'{APP_URL}/login**', timeout=8_000)
        assert '/login' in page.url

    def test_login_page_redirects_already_authenticated_user(self, page: Page):
        _do_login(page)
        page.goto(LOGIN_URL)
        # App should redirect an authenticated user away from /login
        assert '/login' not in page.url


# FlowForgotPasswordUI

@pytest.mark.flow
class FlowForgotPasswordUI:
    """Forgot-password multi-step UI — does not complete an actual reset
    (no valid OTP is available in automation)."""

    @pytest.fixture(autouse=True)
    def navigate_to_reset_step(self, page: Page):
        page.goto(LOGIN_URL)
        page.get_by_role('button', name='Forgot Password?').click()
        page.locator('#forgotEmail').fill(TEST_USER_EMAIL)
        page.get_by_role('button', name='Send Reset OTP').click()
        page.wait_for_selector('text=Reset Password', timeout=8_000)

    def test_reset_step_visible_after_email_submit(self, page: Page):
        expect(page.get_by_role('heading', name='Reset Password')).to_be_visible()

    def test_wrong_otp_shows_error(self, page: Page):
        page.locator('input[data-input-otp="true"]').fill('000000')
        page.locator('#newPassword').fill('NewStrongPass@789')
        page.locator('#confirmPassword').fill('NewStrongPass@789')
        page.wait_for_function(
            "() => ['Weak','Medium','Strong'].some(s => document.body.textContent.includes(s))",
            timeout=8_000,
        )
        page.get_by_role('button', name='Reset Password').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=8_000)

    def test_resend_otp_does_not_crash(self, page: Page):
        page.get_by_role('button', name='Resend OTP').click()
        # Page should stay on the reset step without an unhandled error
        expect(page.get_by_role('heading', name='Reset Password')).to_be_visible(timeout=5_000)

    def test_back_to_login_from_reset_step(self, page: Page):
        page.get_by_role('button', name='Back to Login').click()
        expect(page.get_by_role('heading', name='Welcome back', exact=True)).to_be_visible()


# FlowPendingUserRegistrationUI

@pytest.mark.flow
class FlowPendingUserRegistrationUI:
    """Login as a pending (unverified) user and exercise the Complete Registration UI."""

    @pytest.fixture(autouse=True)
    def navigate_to_pending_step(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(PENDING_USER_EMAIL)
        page.locator('#password').fill(PENDING_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        page.wait_for_selector('text=Complete Registration', timeout=12_000)

    def test_complete_registration_heading_visible(self, page: Page):
        expect(page.get_by_role('heading', name='Complete Registration')).to_be_visible()

    def test_phone_otp_step_ui_elements_present(self, page: Page):
        expect(page.locator('input[data-input-otp="true"]')).to_be_visible()
        expect(page.get_by_role('button', name='Verify Phone')).to_be_visible()
        expect(page.get_by_text('Resend OTP')).to_be_visible()

    def test_wrong_phone_otp_shows_error(self, page: Page):
        page.locator('input[data-input-otp="true"]').fill('000000')
        page.get_by_role('button', name='Verify Phone').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=8_000)

    def test_back_to_login_from_pending_step(self, page: Page):
        page.get_by_role('button', name='Back to login').click()
        expect(page.get_by_role('heading', name='Welcome back', exact=True)).to_be_visible()


# FlowSessionPersistence

@pytest.mark.flow
class FlowSessionPersistence:
    """Sessions survive page refreshes; protected routes stay protected mid-session."""

    def test_session_survives_page_refresh(self, page: Page):
        _do_login(page)
        page.reload()
        page.wait_for_load_state('networkidle')
        assert '/dashboard' in page.url

    def test_login_page_redirects_authenticated_user_mid_session(self, page: Page):
        _do_login(page)
        page.goto(LOGIN_URL)
        assert '/login' not in page.url
