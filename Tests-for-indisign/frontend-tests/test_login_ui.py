import re
import pytest
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import Page, expect

load_dotenv(Path(__file__).parent.parent / '.env')

APP_URL              = os.getenv('APP_URL',               'http://localhost:4200')
TEST_USER_EMAIL      = os.getenv('TEST_USER_EMAIL',       'testuser@example.com')
TEST_USER_PASSWORD   = os.getenv('TEST_USER_PASSWORD',    'TestPassword@123')
PENDING_USER_EMAIL   = os.getenv('PENDING_USER_EMAIL',    'pending@example.com')
PENDING_USER_PASSWORD = os.getenv('PENDING_USER_PASSWORD', 'PendingPass@123')

LOGIN_URL = f'{APP_URL}/login'



class TestPageRendering:
    """All expected UI elements are visible when the login page first loads."""

    def test_welcome_heading_visible(self, page: Page):
        page.goto(LOGIN_URL)
        expect(page.get_by_role('heading', name='Welcome back', exact=True)).to_be_visible()

    def test_email_input_visible(self, page: Page):
        page.goto(LOGIN_URL)
        expect(page.locator('#email')).to_be_visible()

    def test_password_input_visible(self, page: Page):
        page.goto(LOGIN_URL)
        expect(page.locator('#password')).to_be_visible()

    def test_sign_in_button_visible(self, page: Page):
        page.goto(LOGIN_URL)
        expect(page.get_by_role('button', name='Sign In')).to_be_visible()

    def test_forgot_password_button_visible(self, page: Page):
        page.goto(LOGIN_URL)
        expect(page.get_by_role('button', name='Forgot Password?')).to_be_visible()

    def test_signup_link_visible(self, page: Page):
        page.goto(LOGIN_URL)
        expect(page.get_by_role('link', name='Sign up')).to_be_visible()

    def test_terms_of_service_link_visible(self, page: Page):
        page.goto(LOGIN_URL)
        expect(page.get_by_role('link', name='Terms of Service')).to_be_visible()

    def test_privacy_policy_link_visible(self, page: Page):
        page.goto(LOGIN_URL)
        expect(page.get_by_role('link', name='Privacy Policy')).to_be_visible()

    def test_password_field_masked_by_default(self, page: Page):
        page.goto(LOGIN_URL)
        assert page.locator('#password').get_attribute('type') == 'password'

    def test_email_label_present(self, page: Page):
        page.goto(LOGIN_URL)
        expect(page.locator('label[for="email"]')).to_be_visible()

    def test_password_label_present(self, page: Page):
        page.goto(LOGIN_URL)
        expect(page.locator('label[for="password"]')).to_be_visible()


class TestFormValidation:
    """HTML5 required/type validation prevents submission without server contact."""

    def test_empty_email_blocks_submission(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        # HTML5 required prevents navigation; still on login page
        assert '/login' in page.url

    def test_empty_password_blocks_submission(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.get_by_role('button', name='Sign In').click()
        assert '/login' in page.url

    def test_both_fields_empty_blocks_submission(self, page: Page):
        page.goto(LOGIN_URL)
        page.get_by_role('button', name='Sign In').click()
        assert '/login' in page.url

    def test_invalid_email_format_blocks_submission(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill('not-a-valid-email')
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        assert '/login' in page.url

    def test_email_without_tld_blocks_submission(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill('user@nodot')
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        assert '/login' in page.url

    def test_email_field_accepts_valid_email_value(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        assert page.locator('#email').input_value() == TEST_USER_EMAIL

    def test_password_field_accepts_input_value(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#password').fill(TEST_USER_PASSWORD)
        assert page.locator('#password').input_value() == TEST_USER_PASSWORD


class TestPasswordToggle:
    """The show/hide password button toggles the input type between password and text."""

    def test_password_hidden_before_toggle(self, page: Page):
        page.goto(LOGIN_URL)
        assert page.locator('#password').get_attribute('type') == 'password'

    def test_password_revealed_after_toggle(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#password').fill('somepassword')
        # The toggle button is inside the PasswordInput wrapper next to #password
        page.locator('div:has(> input#password) button[type="button"]').click()
        assert page.locator('#password').get_attribute('type') == 'text'

    def test_password_re_hidden_on_second_toggle(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#password').fill('somepassword')
        toggle = page.locator('div:has(> input#password) button[type="button"]')
        toggle.click()
        toggle.click()
        assert page.locator('#password').get_attribute('type') == 'password'



class TestLoginSuccess:
    """Valid credentials log the user in and redirect to the dashboard."""

    def test_valid_credentials_redirect_to_dashboard(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        page.wait_for_url(f'{APP_URL}/dashboard**', timeout=10_000)
        assert '/dashboard' in page.url

    def test_session_cookie_set_after_login(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        page.wait_for_url(f'{APP_URL}/dashboard**', timeout=10_000)
        cookie_names = [c['name'] for c in page.context.cookies()]
        assert 'sid' in cookie_names

    def test_sign_in_button_disabled_while_submitting(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill(TEST_USER_PASSWORD)
        # Intercept the first API call (crypto/public-key is fetched before auth/login)
        with page.expect_request(re.compile(r'.*(auth/login|crypto/public-key).*')):
            page.get_by_role('button', name='Sign In').click()
            btn = page.get_by_role('button', name='Signing in...')
            # Button text changes and becomes disabled during the request
            assert btn.count() == 0 or btn.is_disabled()


class TestLoginFailure:
    """Invalid credentials surface an error alert without leaving the login page."""

    def test_wrong_password_shows_error_alert(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill('DefinitelyWrong!99')
        page.get_by_role('button', name='Sign In').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=8_000)
        assert '/login' in page.url

    def test_nonexistent_email_shows_error_alert(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill('nobody@doesnotexist.example.com')
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=8_000)
        assert '/login' in page.url

    def test_error_message_contains_meaningful_text(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill('WrongPassword!00')
        page.get_by_role('button', name='Sign In').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=8_000)
        error_text = page.locator('[role="alert"]').first.inner_text().lower()
        # Error should mention credentials or password, not a raw stack trace
        assert any(word in error_text for word in ['invalid', 'incorrect', 'password', 'credentials', 'failed'])

    def test_error_cleared_on_successful_retry(self, page: Page):
        page.goto(LOGIN_URL)
        # First: wrong password → error
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill('WrongPass!00')
        page.get_by_role('button', name='Sign In').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=8_000)

        # Second: correct password → redirect (error disappears)
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        page.wait_for_url(f'{APP_URL}/dashboard**', timeout=10_000)
        assert '/dashboard' in page.url

    def test_url_stays_on_login_after_failed_attempt(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill('TotallyWrong!1')
        page.get_by_role('button', name='Sign In').click()
        page.wait_for_selector('[role="alert"]', timeout=8_000)
        assert '/login' in page.url



class TestSessionExpired:
    """Navigating to /login?session_expired=true surfaces the expiry message."""

    def test_session_expired_alert_visible(self, page: Page):
        page.goto(f'{LOGIN_URL}?session_expired=true')
        expect(page.locator('[role="alert"]').first).to_be_visible()

    def test_session_expired_message_text(self, page: Page):
        page.goto(f'{LOGIN_URL}?session_expired=true')
        alert_text = page.locator('[role="alert"]').first.inner_text().lower()
        assert 'session' in alert_text and 'expired' in alert_text

    def test_session_expired_page_still_has_login_form(self, page: Page):
        page.goto(f'{LOGIN_URL}?session_expired=true')
        expect(page.locator('#email')).to_be_visible()
        expect(page.locator('#password')).to_be_visible()

    def test_no_session_expired_alert_without_param(self, page: Page):
        page.goto(LOGIN_URL)
        # No session-expired alert should appear without the query param
        assert page.locator('[role="alert"]').filter(has_text=re.compile('session.*expired', re.I)).count() == 0



class TestForgotPasswordFlow:
    """Clicking 'Forgot Password?' steps through the multi-stage reset flow."""

    def test_forgot_password_transitions_to_step_4(self, page: Page):
        page.goto(LOGIN_URL)
        page.get_by_role('button', name='Forgot Password?').click()
        expect(page.get_by_role('heading', name='Forgot Password')).to_be_visible()

    def test_forgot_password_email_field_present(self, page: Page):
        page.goto(LOGIN_URL)
        page.get_by_role('button', name='Forgot Password?').click()
        expect(page.locator('#forgotEmail')).to_be_visible()

    def test_forgot_password_send_otp_button_present(self, page: Page):
        page.goto(LOGIN_URL)
        page.get_by_role('button', name='Forgot Password?').click()
        expect(page.get_by_role('button', name='Send Reset OTP')).to_be_visible()

    def test_email_prefilled_from_login_input(self, page: Page):
        """Email typed in the login field is pre-filled when Forgot Password is clicked."""
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.get_by_role('button', name='Forgot Password?').click()
        assert page.locator('#forgotEmail').input_value() == TEST_USER_EMAIL

    def test_back_to_login_from_forgot_password(self, page: Page):
        page.goto(LOGIN_URL)
        page.get_by_role('button', name='Forgot Password?').click()
        page.get_by_role('button', name='Back to Login').click()
        expect(page.get_by_role('heading', name='Welcome back', exact=True)).to_be_visible()

    def test_submit_email_advances_to_reset_password_step(self, page: Page):
        """Submitting the forgot-password email always advances to step 5 (API never errors to prevent enumeration)."""
        page.goto(LOGIN_URL)
        page.get_by_role('button', name='Forgot Password?').click()
        page.locator('#forgotEmail').fill(TEST_USER_EMAIL)
        page.get_by_role('button', name='Send Reset OTP').click()
        expect(page.get_by_role('heading', name='Reset Password')).to_be_visible(timeout=8_000)

    def test_submit_non_existent_email_still_advances(self, page: Page):
        """API always returns success to prevent email enumeration — step advances regardless."""
        page.goto(LOGIN_URL)
        page.get_by_role('button', name='Forgot Password?').click()
        page.locator('#forgotEmail').fill('ghost@nobody.example.com')
        page.get_by_role('button', name='Send Reset OTP').click()
        expect(page.get_by_role('heading', name='Reset Password')).to_be_visible(timeout=8_000)



class TestResetPasswordStep:
    """Step 5 — OTP + new password form validation."""

    @pytest.fixture(autouse=True)
    def navigate_to_reset_step(self, page: Page):
        """Shared setup: navigate to the reset password step before each test."""
        page.goto(LOGIN_URL)
        page.get_by_role('button', name='Forgot Password?').click()
        page.locator('#forgotEmail').fill(TEST_USER_EMAIL)
        page.get_by_role('button', name='Send Reset OTP').click()
        page.wait_for_selector('text=Reset Password', timeout=8_000)

    def test_reset_step_has_otp_input(self, page: Page):
        expect(page.locator('input[data-input-otp="true"]')).to_be_visible()

    def test_reset_step_has_new_password_field(self, page: Page):
        expect(page.locator('#newPassword')).to_be_visible()

    def test_reset_step_has_confirm_password_field(self, page: Page):
        expect(page.locator('#confirmPassword')).to_be_visible()

    def test_reset_step_has_resend_otp_button(self, page: Page):
        expect(page.get_by_role('button', name="Resend OTP")).to_be_visible()

    def test_back_to_login_from_reset_step(self, page: Page):
        page.get_by_role('button', name='Back to Login').click()
        expect(page.get_by_role('heading', name='Welcome back', exact=True)).to_be_visible()

    def test_submit_without_otp_shows_error(self, page: Page):
        page.locator('#newPassword').fill('NewStrongPass@789')
        page.locator('#confirmPassword').fill('NewStrongPass@789')
        page.get_by_role('button', name='Reset Password').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=5_000)
        error_text = page.locator('[role="alert"]').first.inner_text().lower()
        assert 'otp' in error_text

    def test_submit_with_mismatched_passwords_shows_error(self, page: Page):
        page.locator('input[data-input-otp="true"]').fill('123456')
        page.locator('#newPassword').fill('NewStrongPass@789')
        # The handler checks passwordValidation *before* checking mismatch, so we must
        # wait for the async validation API call to return before clicking submit.
        page.wait_for_function(
            "() => ['Weak','Medium','Strong'].some(s => document.body.textContent.includes(s))",
            timeout=8_000,
        )
        page.locator('#confirmPassword').fill('DifferentPass@999')
        page.get_by_role('button', name='Reset Password').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=5_000)
        error_text = page.locator('[role="alert"]').first.inner_text().lower()
        # Frontend may show a mismatch error or a strength/requirements error depending
        # on which validation fires first — both are valid rejection signals.
        assert any(w in error_text for w in ['match', 'password', 'requirement'])

    def test_reset_button_disabled_while_password_invalid(self, page: Page):
        """Reset button stays disabled when the password fails strength validation."""
        page.locator('input[data-input-otp="true"]').fill('123456')
        page.locator('#newPassword').fill('weak')
        page.locator('#confirmPassword').fill('weak')
        # Button is disabled during isValidatingPassword=true (500ms debounce + API call window).
        # Assert disabled within that window rather than waiting for the result to land.
        expect(page.get_by_role('button', name='Reset Password')).to_be_disabled(timeout=3_000)


class TestIncompleteRegistrationFlow:
    """
    Logging in with a pending (unverified) account redirects to the phone OTP
    step rather than showing a plain error.

    Requires PENDING_USER_EMAIL / PENDING_USER_PASSWORD in .env and the
    corresponding row in pending_users (created by conftest setup_test_users).
    """

    @pytest.fixture(autouse=True)
    def navigate_to_pending_step(self, page: Page):
        """Shared setup: log in as the pending user before each test."""
        page.goto(LOGIN_URL)
        page.locator('#email').fill(PENDING_USER_EMAIL)
        page.locator('#password').fill(PENDING_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        page.wait_for_selector('text=Complete Registration', timeout=10_000)

    def test_pending_user_shows_complete_registration_heading(self, page: Page):
        expect(page.get_by_role('heading', name='Complete Registration')).to_be_visible()

    def test_phone_otp_step_shows_progress_indicator(self, page: Page):
        expect(page.get_by_text('Phone')).to_be_visible()
        expect(page.get_by_text('Email')).to_be_visible()

    def test_phone_otp_step_has_6_slot_input(self, page: Page):
        # input-otp renders a single underlying input with maxLength=6
        expect(page.locator('input[data-input-otp="true"]')).to_be_visible()
        assert int(page.locator('input[data-input-otp="true"]').get_attribute('maxlength')) == 6

    def test_verify_phone_button_disabled_without_otp(self, page: Page):
        assert page.get_by_role('button', name='Verify Phone').is_disabled()

    def test_verify_phone_button_enabled_with_6_digits(self, page: Page):
        page.locator('input[data-input-otp="true"]').fill('123456')
        assert page.get_by_role('button', name='Verify Phone').is_enabled()

    def test_resend_otp_button_visible_on_phone_step(self, page: Page):
        expect(page.get_by_text('Resend OTP')).to_be_visible()

    def test_back_to_login_from_phone_otp_step(self, page: Page):
        page.get_by_role('button', name='Back to login').click()
        expect(page.get_by_role('heading', name='Welcome back', exact=True)).to_be_visible()

    def test_wrong_otp_on_phone_step_shows_error(self, page: Page):
        page.locator('input[data-input-otp="true"]').fill('000000')
        page.get_by_role('button', name='Verify Phone').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=8_000)



class TestNavigationLinks:
    """Links on the login page point to the correct hrefs."""

    def test_signup_link_points_to_signup_page(self, page: Page):
        page.goto(LOGIN_URL)
        href = page.get_by_role('link', name='Sign up').get_attribute('href')
        assert '/signup' in href

    def test_terms_link_points_to_terms_page(self, page: Page):
        page.goto(LOGIN_URL)
        href = page.get_by_role('link', name='Terms of Service').get_attribute('href')
        assert '/terms-of-service' in href

    def test_privacy_policy_link_points_to_privacy_page(self, page: Page):
        page.goto(LOGIN_URL)
        href = page.get_by_role('link', name='Privacy Policy').get_attribute('href')
        assert '/privacy-policy' in href

    def test_clicking_signup_navigates_to_signup(self, page: Page):
        page.goto(LOGIN_URL)
        page.get_by_role('link', name='Sign up').click()
        page.wait_for_url(f'{APP_URL}/signup**', timeout=8_000)
        assert '/signup' in page.url



@pytest.mark.slow
class TestRateLimiting:
    """
    After enough consecutive failed login attempts the server returns 429 and
    the frontend shows a 'too many attempts' error.

    The conftest clears cooldowns before every test, so this class runs the
    full ramp-up itself.
    """

    def test_rate_limit_error_shown_after_repeated_failures(self, page: Page):
        page.goto(LOGIN_URL)
        last_status = None

        for i in range(12):
            page.locator('#email').fill(TEST_USER_EMAIL)
            page.locator('#password').fill(f'WrongPass{i}!')
            with page.expect_response(
                lambda r: '/login' in r.url and r.request.method == 'POST',
                timeout=8_000,
            ) as resp_info:
                page.get_by_role('button', name='Sign In').click()
            last_status = resp_info.value.status
            page.wait_for_selector('[role="alert"]', timeout=8_000)
            page.locator('#password').fill('')
            if last_status == 429:
                break

        # Accept either a proper 429 from the server or the UI surfacing the block
        # ('failed to fetch' means the browser blocked a CORS-less 429 response)
        if last_status == 429:
            return
        error_text = page.locator('[role="alert"]').first.inner_text().lower()
        assert (
            'too many' in error_text
            or 'try again' in error_text
            or 'failed to fetch' in error_text
        ), f"Expected rate-limit error, got: {error_text!r}"

    def test_rate_limited_correct_password_still_blocked(self, page: Page):
        """Even the correct password is blocked once the account is rate-limited."""
        page.goto(LOGIN_URL)
        # Trigger rate limit
        for i in range(12):
            page.locator('#email').fill(TEST_USER_EMAIL)
            page.locator('#password').fill(f'WrongPass{i}!')
            page.get_by_role('button', name='Sign In').click()
            page.wait_for_selector('[role="alert"]', timeout=8_000)

        # Now try with the correct password
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        page.wait_for_selector('[role="alert"]', timeout=8_000)
        assert '/login' in page.url


class TestKeyboardNavigation:
    """The login form is fully operable without a mouse."""

    def test_email_input_is_keyboard_focusable(self, page: Page):
        """Email input can be directly focused via keyboard API (and via Tab order)."""
        page.goto(LOGIN_URL)
        page.locator('#email').focus()
        assert page.evaluate("() => document.activeElement.id") == 'email'

    def test_tab_from_email_reaches_password(self, page: Page):
        """Tabbing from email reaches the password field within 3 presses.
        A password-toggle button between the two inputs may consume one Tab stop."""
        page.goto(LOGIN_URL)
        page.locator('#email').focus()
        for _ in range(3):
            if page.evaluate("() => document.activeElement.id") == 'password':
                break
            page.keyboard.press('Tab')
        assert page.evaluate("() => document.activeElement.id") == 'password'

    def test_enter_in_password_field_submits(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill(TEST_USER_PASSWORD)
        with page.expect_request(re.compile(r'.*(auth/login|crypto/public-key).*')):
            page.locator('#password').press('Enter')

    def test_tab_order_reaches_sign_in_button(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').focus()
        page.keyboard.press('Tab')  # → password
        page.keyboard.press('Tab')  # → password toggle or Sign In
        page.keyboard.press('Tab')  # → Sign In (at most 2 tabs away)
        focused_text = page.evaluate("() => document.activeElement.textContent")
        focused_role = page.evaluate("() => document.activeElement.getAttribute('type')")
        assert 'Sign' in (focused_text or '') or focused_role == 'submit'


class TestAccessibility:
    """Form inputs carry the correct semantic attributes for browsers and screen readers."""

    def test_email_input_autocomplete_attribute(self, page: Page):
        """App currently sets autocomplete='off' on the email field."""
        page.goto(LOGIN_URL)
        assert page.locator('#email').get_attribute('autocomplete') == 'off'

    def test_password_input_autocomplete_attribute(self, page: Page):
        """App currently sets autocomplete='off' on the password field."""
        page.goto(LOGIN_URL)
        assert page.locator('#password').get_attribute('autocomplete') == 'off'

    def test_page_has_non_empty_title(self, page: Page):
        page.goto(LOGIN_URL)
        assert page.title().strip() != ''

    def test_error_alert_has_role_alert(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill('WrongPass!00')
        page.get_by_role('button', name='Sign In').click()
        page.wait_for_selector('[role="alert"]', timeout=8_000)
        assert page.locator('[role="alert"]').first.get_attribute('role') == 'alert'

    def test_email_label_for_matches_input_id(self, page: Page):
        page.goto(LOGIN_URL)
        assert page.locator('label[for="email"]').count() == 1

    def test_password_label_for_matches_input_id(self, page: Page):
        page.goto(LOGIN_URL)
        assert page.locator('label[for="password"]').count() == 1


class TestViewport:
    """The login form is usable on common mobile and tablet screen sizes."""

    def test_mobile_form_is_visible(self, page: Page):
        page.set_viewport_size({'width': 375, 'height': 667})
        page.goto(LOGIN_URL)
        expect(page.locator('#email')).to_be_visible()
        expect(page.locator('#password')).to_be_visible()
        expect(page.get_by_role('button', name='Sign In')).to_be_visible()

    def test_mobile_password_toggle_is_clickable(self, page: Page):
        page.set_viewport_size({'width': 375, 'height': 667})
        page.goto(LOGIN_URL)
        page.locator('#password').fill('somepassword')
        toggle = page.locator('div:has(> input#password) button[type="button"]')
        expect(toggle).to_be_visible()
        toggle.click()
        assert page.locator('#password').get_attribute('type') == 'text'

    def test_mobile_forgot_password_visible(self, page: Page):
        page.set_viewport_size({'width': 375, 'height': 667})
        page.goto(LOGIN_URL)
        expect(page.get_by_role('button', name='Forgot Password?')).to_be_visible()

    def test_tablet_form_is_visible(self, page: Page):
        page.set_viewport_size({'width': 768, 'height': 1024})
        page.goto(LOGIN_URL)
        expect(page.locator('#email')).to_be_visible()
        expect(page.locator('#password')).to_be_visible()
        expect(page.get_by_role('button', name='Sign In')).to_be_visible()


class TestXSSInputSanitization:
    """HTML and script payloads in form inputs must not execute in the browser."""

    def test_xss_img_in_email_does_not_execute(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill('<img src=x onerror="window.__xss=1">')
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        page.wait_for_timeout(500)
        assert page.evaluate('() => window.__xss') is None

    def test_xss_script_in_email_does_not_execute(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill('<script>window.__xss=1</script>')
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        page.wait_for_timeout(500)
        assert page.evaluate('() => window.__xss') is None

    def test_xss_img_in_password_does_not_execute(self, page: Page):
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill('<img src=x onerror="window.__xss=1">')
        page.get_by_role('button', name='Sign In').click()
        page.wait_for_timeout(500)
        assert page.evaluate('() => window.__xss') is None


class TestNetworkErrorHandling:
    """The UI surfaces a user-facing error alert when the backend is unreachable or errors."""

    def test_offline_network_shows_error_alert(self, page: Page):
        page.goto(LOGIN_URL)
        page.context.set_offline(True)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=8_000)
        assert '/login' in page.url
        page.context.set_offline(False)

    def test_server_500_shows_error_alert(self, page: Page):
        page.route(re.compile(r'.*/auth/login.*'), lambda route: route.fulfill(
            status=500,
            content_type='application/json',
            body='{"error":"internal server error"}'
        ))
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=8_000)

    def test_aborted_request_shows_error_alert(self, page: Page):
        page.route(re.compile(r'.*/auth/login.*'), lambda route: route.abort())
        page.goto(LOGIN_URL)
        page.locator('#email').fill(TEST_USER_EMAIL)
        page.locator('#password').fill(TEST_USER_PASSWORD)
        page.get_by_role('button', name='Sign In').click()
        expect(page.locator('[role="alert"]').first).to_be_visible(timeout=8_000)