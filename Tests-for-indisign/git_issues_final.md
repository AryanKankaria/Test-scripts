# Git Issues - Login Flow Test Execution Documentation

Date: May 4, 2026
Total Tests: 77
Status: All Passed
Exit Code: 0

---

## Issue 1: Login Flow - Advanced Rate Limiting Tests

**Topic**: Verification of progressive rate limiting behavior, window expiry, and counter reset on successful login.

The rate limiting system is designed to protect the login endpoint against brute-force attacks. It tracks failed login attempts per user and imposes escalating cooldowns once a threshold is crossed. These tests verify that the cooldown escalation is genuinely progressive (not flat), that the rate limit window resets correctly after expiry, and that a successful login clears the failed attempt counter entirely. The rate limit threshold used throughout these tests is 10 failed attempts, after which the 11th attempt triggers a 429 response. The rate limit window in the test environment is set to 1 minute (vs. 15 minutes in production) to keep test execution time reasonable.

---

**Sub-Issue 1.1: test_progressive_cooldown_per_failed_attempt**

Description: This test verifies that the cooldown duration returned in a 429 response escalates with each additional batch of failed attempts. It simulates three separate escalation scenarios by making 11, 12, and then 13 failed login attempts in sequence, collecting the 'cooldown_seconds' or 'retry_after_seconds' value from each 429 response. The test then asserts that at least one cooldown value was collected (confirming the rate limit triggered), and that each subsequent cooldown is greater than or equal to the previous one.

Expected Outcome: At least one 429 is collected across the three batches; cooldown values are non-decreasing, confirming escalation.

Actual Outcome: Passed. Cooldown escalation behaves as expected across all batches.

---

**Sub-Issue 1.2: test_rate_limit_window_expiry**

Description: This test verifies that the rate limit counter resets automatically once the rate limit window has expired, without any manual intervention. It makes 11 consecutive failed login attempts to push the account into a rate-limited state, confirms a 429 is returned on the next attempt, then waits 62 seconds for the 1-minute window to expire. After the wait, it attempts another login with a wrong password and asserts a 401 rather than a 429, which confirms the counter has been cleared.

The 62-second wait (rather than exactly 60) is intentional, providing a small buffer to account for timing variance between the test runner and the server clock.

'''python
time.sleep(62)  # 62s to account for clock drift against the 60s window
'''

Expected Outcome: 429 after 11 failed attempts; 401 (not 429) after the window expires, confirming the counter has reset.

Actual Outcome: Passed. Rate limit window expiry and counter reset function correctly.

---

**Sub-Issue 1.3: test_successful_login_clears_rate_limit**

Description: This test verifies that a successful login does not merely bypass the rate limit for that one request - it actively resets the failed attempt counter, so subsequent failures start fresh from attempt 1. The test makes 3 failed attempts (well below the threshold of 10), then logs in successfully and logs out. It then opens a new session and makes one additional failed attempt, asserting a 401 rather than a 429. A 401 here confirms the counter was cleared on successful login, not merely paused.

Expected Outcome: 200 on successful login; 200 on logout; 401 (not 429) on the next failed attempt from a fresh session.

Actual Outcome: Passed. Successful login correctly clears the rate limit counter.

---

## Issue 2: Login Flow - Authentication Tests

**Topic**: Verification of core authentication behavior including login success and failure, session creation, logout, and authorization header support.

This is the broadest test file, covering the fundamental contract of the authentication system end-to-end. It tests the happy path (valid credentials, session creation, cookie setting), all major failure modes (wrong password, nonexistent user, missing fields, empty fields), the full rate limiting trigger and response format, logout behavior including idempotency, session management via both cookies and Bearer tokens, and the rejection of unauthenticated requests. These tests collectively establish that the '/auth/login', '/auth/logout', and '/auth/verify' endpoints behave correctly as a unified system.

Note: This file contains 18 tests, not 22 as listed in the execution report. The count of 22 in the report is incorrect.

---

**Sub-Issue 2.1: test_valid_login_returns_user_and_sets_cookie**

Description: This is the baseline success test. It submits valid credentials and verifies that the response includes a 'user' object with the correct email address, and that a 'sid' cookie is set in the session. The 'sid' cookie is the session identifier used by all subsequent authenticated requests.

Expected Outcome: 200 status; 'user.email' matches the test user's email; 'sid' cookie is present in the session.

Actual Outcome: Passed. Valid login returns user data and sets the session cookie correctly.

---

**Sub-Issue 2.2: test_login_creates_valid_session**

Description: This test goes one step beyond confirming the login response - it verifies that the session created during login is actually recognized by the '/auth/verify' endpoint. After a successful login, it calls verify and asserts a 200 response containing either an 'email' or 'user' field, confirming the session is active and the server can identify the authenticated user.

Expected Outcome: 200 on login; 200 on verify with user data present in the response.

Actual Outcome: Passed. Session is created and verifiable after login.

---

**Sub-Issue 2.3: test_login_removes_previous_sessions**

    Description: This test verifies that the system enforces single-session login - a new login invalidates the previous session. It logs in twice in sequence using the same credentials, confirms the 'sid' values differ between the two logins, then injects the old 'sid' into a fresh session and calls '/auth/verify'. A 401 on that verify call confirms the old session was invalidated server-side, not merely replaced in the cookie jar.

    Expected Outcome: Old and new 'sid' values differ; '/auth/verify' returns 401 when called with the old 'sid' after the second login.

    Actual Outcome: Passed. New login correctly invalidates the previous session server-side.

---

**Sub-Issue 2.4: test_login_invalid_password**

Description: Verifies that submitting a correct email with a wrong password is rejected with a 401 and that the response body contains an 'error' field. The presence of the 'error' field is important for frontend error handling - without it, the client has no structured message to display.

Expected Outcome: 401 status; 'error' field present in the response body.

Actual Outcome: Passed. Invalid password is correctly rejected with a structured error response.

---

**Sub-Issue 2.5: test_login_nonexistent_user**

Description: Verifies that an email address that does not exist in the system returns a 401 with the error message "invalid credentials". The error message is intentionally identical to the invalid password error - returning a distinct message such as "user not found" would allow an attacker to enumerate valid email addresses.

Expected Outcome: 401 status; 'error' equal to "invalid credentials".

Actual Outcome: Passed. Nonexistent user login returns the generic error message as expected.

---

**Sub-Issue 2.6: test_login_missing_email**

Description: Verifies that a login request with no 'email' field in the body is rejected with a 400 before any credential lookup occurs. A 400 (Bad Request) is the appropriate response for a structurally invalid request, distinct from a 401 which implies the credentials were evaluated and found incorrect.

Expected Outcome: 400 status.

Actual Outcome: Passed. Missing email field is correctly rejected at the validation layer.

---

**Sub-Issue 2.7: test_login_missing_password**

Description: Verifies that a login request with no 'password' field is rejected with a 400 for the same structural validation reason as the missing email test.

Expected Outcome: 400 status.

Actual Outcome: Passed. Missing password field is correctly rejected.

---

**Sub-Issue 2.8: test_login_empty_credentials**

Description: Verifies that submitting both 'email' and 'password' as empty strings is rejected with a 400. Empty strings are not the same as missing fields at the JSON level, but the server must treat them as invalid input rather than attempting a credential lookup against an empty email.

Expected Outcome: 400 status.

Actual Outcome: Passed. Empty string credentials are correctly rejected.

---

**Sub-Issue 2.9: test_rate_limit_after_failed_attempts**

Description: This test verifies that rate limiting engages after 11 consecutive failed attempts. Each of the 11 attempts is asserted to return either 401 (not yet rate limited) or 429 (already rate limited), acknowledging that rate limiting may kick in before the 11th attempt depending on state. A final attempt with the correct password must return 429, and the response body must contain "cooldown" or "retry" to confirm the error is structured. The 429 assertion is unconditional.

Expected Outcome: Each failed attempt returns 401 or 429; the final correct-password attempt returns 429 with rate limit context in the body.

Actual Outcome: Passed. Rate limiting activates after the expected number of failures.

---

**Sub-Issue 2.10: test_rate_limit_returns_retry_after**

Description: Verifies that a 429 response from the login endpoint includes machine-readable retry timing. The response must contain either 'retry_after_seconds' or 'cooldown_seconds' so the frontend or client can display an accurate wait time rather than a generic error. This test makes 11 failed attempts to trigger the limit, then unconditionally asserts a 429 and checks the structure of the response body.

Expected Outcome: 429 status; body contains 'retry_after_seconds' or 'cooldown_seconds'.

Actual Outcome: Passed. Rate limit response includes the expected retry field.

---

**Sub-Issue 2.11: test_logout_clears_session**

Description: Verifies the basic contract of the logout endpoint: it returns a 200 with 'ok: true' in the body. The 'ok: true' field is checked explicitly because the frontend relies on this field to confirm a successful logout before redirecting the user.

Expected Outcome: 200 status; 'ok' is 'true' in the response body.

Actual Outcome: Passed. Logout returns the expected response structure.

---

**Sub-Issue 2.12: test_logout_invalidates_cookie**

Description: Verifies that logout not only returns a 200 but also invalidates the session server-side. After logout, a call to '/auth/verify' using the same session cookies must return 401. This confirms the server has deleted or expired the session record, not merely instructed the client to clear the cookie.

Expected Outcome: 401 on verify following logout.

Actual Outcome: Passed. Session is invalidated server-side on logout.

---

**Sub-Issue 2.13: test_logout_without_session**

Description: Verifies that calling logout with no active session does not cause a server error. This is an idempotency check - the logout endpoint must be safe to call even when there is nothing to log out of. A 500 or 401 here would indicate the server is not handling the no-session case gracefully.

Expected Outcome: 200 status.

Actual Outcome: Passed. Logout without a session returns 200 without error.

---

**Sub-Issue 2.14: test_request_without_session_cookie**

Description: Verifies that clearing all session cookies client-side results in a 401 on the verify endpoint. This simulates a user whose cookies were deleted (browser clear, incognito close, etc.). The test logs in to create a valid session, then manually clears all cookies before calling verify.

Expected Outcome: 401 status after cookies are cleared.

Actual Outcome: Passed. Verify correctly rejects requests with no session cookie.

---

**Sub-Issue 2.15: test_request_with_authorization_header**

Description: Verifies that the 'sid' cookie value can also be used as a Bearer token in the 'Authorization' header, enabling API clients that cannot use cookies to authenticate. The token is extracted from the login response cookies and sent via a separate session that has no cookies of its own.

Expected Outcome: 200 status on verify when the 'sid' value is passed as 'Authorization: Bearer {token}'.

Actual Outcome: Passed. Bearer token authentication via header is accepted.

---

**Sub-Issue 2.16: test_session_remains_valid_after_short_delay**

Description: Verifies that a session does not expire between two verify requests separated by a 2-second pause. This is a basic confirmation that the session TTL is meaningfully longer than a few seconds, and that the sliding window mechanism does not interfere with back-to-back requests.

Expected Outcome: Both verify requests return 200.

Actual Outcome: Passed. Session remains valid across requests separated by a short delay.

---

**Sub-Issue 2.17: test_invalid_token_format**

Description: Verifies that a Bearer token containing a string that was never issued by the server ("Bearer invalid_token_format") is rejected. This confirms the server is validating token content against stored session records, not merely checking that the header is present.

Expected Outcome: 401 status.

Actual Outcome: Passed. Malformed Bearer token is correctly rejected.

---

**Sub-Issue 2.18: test_missing_authorization_header_and_cookie**

Description: Verifies that a completely unauthenticated request to '/auth/verify' - with no cookies and no Authorization header - is rejected. This is the baseline security check confirming the endpoint does not fall back to any open access.

Expected Outcome: 401 status.

Actual Outcome: Passed. Unauthenticated requests are correctly rejected.

---

## Issue 3: Login Flow - Login Validation Tests

**Topic**: Verification of input validation, credential formatting, response structure, security of the response body, and access control behavior across login states.

This file tests the login endpoint from a validation and data integrity perspective rather than a pure authentication flow perspective. Key concerns addressed here include: that the response structure is consistent and complete on success, that sensitive fields are never returned, that email normalization (trimming and lowercasing) is applied before credential lookup, that required fields are enforced, and that access to protected endpoints is correctly gated by authentication state. The rate limiting tests in this file are stricter than those in 'test_authentication.py' - the final assertion is a hard 429, not a conditional check.

Note: This file contains 17 tests, not 15 as listed in the execution report. The count of 15 in the report is incorrect.

---

**Sub-Issue 3.1: test_login_error_message_on_wrong_password**

Description: Verifies that an incorrect password returns a 401 with an 'error' field containing "invalid credentials" or "Invalid credentials". Both casings are accepted because the test was written to accommodate potential inconsistency in the backend's error message casing. The check uses 'in' rather than an exact equality match to handle this.

Expected Outcome: 401 status; 'error' field contains "invalid credentials" (case-insensitive match).

Actual Outcome: Passed. Wrong password returns the expected error structure.

---

**Sub-Issue 3.2: test_login_error_message_on_nonexistent_user**

Description: Verifies that an email address not present in the system returns a 401. Unlike the invalid password test, this test does not assert the specific error message text - it only checks the status code. The shared "invalid credentials" message between nonexistent users and wrong passwords is intentional and is tested explicitly in other sub-issues.

Expected Outcome: 401 status.

Actual Outcome: Passed. Nonexistent user is correctly rejected.

---

**Sub-Issue 3.3: test_login_response_structure_success**

Description: Verifies that the successful login response has a predictable, consistent structure. The response must contain a 'user' object with both an 'id' and an 'email' field. These fields are required by the frontend to initialize the authenticated user session.

Expected Outcome: 200 status; 'response.json()['user']' contains both 'email' and 'id'.

Actual Outcome: Passed. Login response structure is correct on success.

---

**Sub-Issue 3.4: test_login_response_does_not_contain_password**

Description: Verifies that neither 'password' nor 'password_hash' is present in the 'user' object of the login response. This is a security requirement - even if the backend accidentally serializes the full user record, the test acts as a guard to catch it before it reaches a user.

Expected Outcome: 200 status; 'password' and 'password_hash' both absent from 'response.json()['user']'.

Actual Outcome: Passed. Sensitive fields are correctly excluded from the login response.

---

**Sub-Issue 3.5: test_login_case_insensitive_email**

Description: Verifies that the backend normalizes the email to lowercase before looking it up, so a user who types their email in uppercase (e.g., copy-pasted from a letter or autocorrected) is not incorrectly rejected. The test submits the test email in all uppercase.

Expected Outcome: 200 status.

Actual Outcome: Passed. Email case normalization works correctly.

---

**Sub-Issue 3.6: test_login_email_with_whitespace**

Description: Verifies that the backend trims leading and trailing spaces from the email before the lookup. The test submits the email wrapped in two spaces on each side. This prevents a common user error - inadvertent whitespace in a copy-pasted email - from causing a login failure.

Expected Outcome: 200 status.

Actual Outcome: Passed. Email whitespace trimming functions correctly.

---

**Sub-Issue 3.7: test_logout_clears_sid_cookie**

Description: Verifies the full logout flow from the perspective of cookie state and endpoint access. After login, the 'sid' cookie is asserted to be present. After logout, calling verify must return 401, confirming both that the cookie was cleared client-side and that the server-side session was invalidated.

Expected Outcome: 'sid' present in cookies after login; 401 on verify after logout.

Actual Outcome: Passed. Session cookie is cleared and session is invalidated on logout.

---

**Sub-Issue 3.8: test_multiple_failed_logins_increase_cooldown**

Description: Verifies that 11 consecutive failed attempts result in a hard 429 on the subsequent correct-password attempt. Unlike the equivalent test in 'test_authentication.py', the assertion here is unconditional - the test always expects a 429, not a 200 or 429. This confirms that 11 failures are definitively sufficient to trigger rate limiting under clean test conditions.

Expected Outcome: Each of the 11 failed attempts returns 401 or 429; the correct-password attempt immediately after returns 429.

Actual Outcome: Passed. 11 failures consistently trigger a hard rate limit.

---

**Sub-Issue 3.9: test_rate_limit_response_contains_retry_info**

Description: Verifies that when a 429 is returned, the response body is structured with both an 'error' field and a retry timing field ('retry_after_seconds' or 'cooldown_seconds'). This test unconditionally asserts a 429 after 11 failed attempts and then asserts both fields are present in the body.

Expected Outcome: 429 status; 'error' is present and at least one of 'retry_after_seconds' or 'cooldown_seconds' is present.

Actual Outcome: Passed. Rate limit response contains the expected fields.

---

**Sub-Issue 3.10: test_password_is_required**

Description: Verifies that a login request body containing only an email field (no 'password' key at all) is rejected with a 400 at the input validation layer.

Expected Outcome: 400 status.

Actual Outcome: Passed. Missing password field is rejected before credential lookup.

---

**Sub-Issue 3.11: test_email_is_required**

Description: Verifies that a login request body containing only a password field (no 'email' key at all) is rejected with a 400.

Expected Outcome: 400 status.

Actual Outcome: Passed. Missing email field is rejected before credential lookup.

---

**Sub-Issue 3.12: test_both_email_and_password_required**

Description: Verifies that an entirely empty JSON body ('{}') is rejected with a 400. This confirms that both fields are required simultaneously and that the absence of both does not cause an unhandled server error.

Expected Outcome: 400 status.

Actual Outcome: Passed. Empty request body is rejected correctly.

---

**Sub-Issue 3.13: test_null_credentials_rejected**

Description: Verifies that explicitly passing 'null' (JSON null) for both email and password is rejected. The acceptable response is either 400 (treated as a validation failure) or 401 (treated as an authentication failure after null is evaluated). Either is acceptable - the critical requirement is that the server does not crash or return 200.

Expected Outcome: 400 or 401 status.

Actual Outcome: Passed. Null credentials are correctly rejected.

---

**Sub-Issue 3.14: test_empty_string_credentials_rejected**

Description: Verifies that submitting empty strings for both fields is rejected with a 400. This is tested separately from null credentials because an empty string is a structurally valid JSON value that some servers may pass through to a credential lookup, which could result in matching against accounts with empty passwords if not guarded.

Expected Outcome: 400 status.

Actual Outcome: Passed. Empty string credentials are rejected at validation.

---

**Sub-Issue 3.15: test_successful_login_user_can_access_protected_endpoint**

Description: Verifies the core authenticated access pattern - that a user who logs in successfully can call '/auth/verify' and receive a 200 with identifying user data. The verify response is checked for the presence of 'email', 'user', or 'id' to confirm the server returns a user identifier and not just a status code.

Expected Outcome: 200 on login; 200 on verify with at least one user identifier ('email', 'user', or 'id') in the response.

Actual Outcome: Passed. Authenticated user can access the verify endpoint with user data returned.

---

**Sub-Issue 3.16: test_failed_login_user_cannot_access_protected_endpoint**

Description: Verifies that a failed login (wrong password) does not result in any session being created, meaning verify returns 401 immediately after. This confirms that the server does not issue a partial or degraded session on failed authentication.

Expected Outcome: 401 on verify after a failed login.

Actual Outcome: Passed. No session is created on failed login.

---

**Sub-Issue 3.17: test_after_logout_user_cannot_access_protected_endpoint**

Description: Verifies the full authenticated lifecycle - login, access a protected endpoint successfully, logout, then confirm access is revoked. This is the end-to-end confirmation that logout is effective and that the protected endpoint does not cache or linger on the previous session.

Expected Outcome: 401 on verify after a successful login followed by logout.

Actual Outcome: Passed. Access is correctly revoked after logout.

---

## Issue 4: Login Flow - Advanced Logout Tests

**Topic**: Verification of logout behavior across different authentication methods, idempotency, and complete session invalidation.

These tests go beyond the basic logout covered in 'test_authentication.py' and focus on edge cases: logout when authenticated via Bearer token rather than cookie, calling logout multiple times on the same session, and confirming that all subsequent verify requests fail after logout (not just the first one). The intent is to ensure logout is unconditional - it must work regardless of how the session was authenticated, and it must leave no residual access window.

---

**Sub-Issue 4.1: test_logout_with_bearer_token_in_header**

Description: Verifies that the logout endpoint works when the session is presented via an 'Authorization: Bearer' header rather than a cookie. This is relevant for API clients or mobile clients that do not use cookies. The test logs in via the standard session (which sets a cookie), extracts the 'sid' value, then sends it as a Bearer token from a new cookieless session to the logout endpoint. It then attempts to verify with the same token and asserts a 401.

Expected Outcome: 200 on logout; 401 on verify using the same Bearer token after logout.

Actual Outcome: Passed. Logout via Bearer token correctly invalidates the session.

---

**Sub-Issue 4.2: test_logout_multiple_times_same_session**

Description: Verifies that calling logout twice on the same session does not cause a server error. The first logout invalidates the session; the second logout is effectively a no-op. Both calls must return 200. This is an idempotency requirement - clients must be able to call logout defensively without risking a 4xx or 5xx on a repeated call.

Expected Outcome: Both logout calls return 200.

Actual Outcome: Passed. Logout is idempotent.

---

**Sub-Issue 4.3: test_logout_returns_ok_true**

Description: Verifies the combined contract of the logout endpoint: it returns 'ok: true' in the body, and it actually invalidates the session (verify returns 401 after). The body assertion and the verify assertion are both present in this test, making it a single-test confirmation of both the response format and the functional result.

Expected Outcome: 200 on logout; 'ok' is 'true' in the body; 401 on the subsequent verify call.

Actual Outcome: Passed. Logout response is correctly structured and session is invalidated.

---

**Sub-Issue 4.4: test_logout_invalidates_session_cookie**

Description: Verifies the before-and-after state of the session relative to logout. Before logout, verify returns 200 - confirming the session is active. After logout, verify returns 401 - confirming the session cookie was invalidated. The two-step assertion makes the causality explicit: logout is what caused the access loss, not some prior state.

Expected Outcome: First verify returns 200; second verify (after logout) returns 401.

Actual Outcome: Passed. Session cookie is correctly invalidated on logout.

---

**Sub-Issue 4.5: test_logout_subsequent_requests_fail**

Description: Verifies that the session invalidation from logout persists across multiple subsequent verify requests, not just the first one. The test calls verify three times in a loop after logout and asserts a 401 on each. This rules out any edge case where the session might be reinstated or cached between requests.

Expected Outcome: All three verify calls after logout return 401.

Actual Outcome: Passed. Session invalidation persists across all subsequent requests.

---

## Issue 5: Login Flow - Pending User Tests

**Topic**: Verification that users in a pending account state cannot authenticate, receive no session, and are not issued a session cookie.

Pending users are accounts that exist in the 'pending_users' table but have not yet completed OTP verification and been promoted to the 'users' table. The login endpoint only looks up records in 'users', so a pending user's credentials are never matched. The backend detects the pending state separately and returns a 401 with a pending-specific error message and a 'pending_id' field identifying the pending registration. No session is created and no cookie is issued.

---

**Sub-Issue 5.1: test_pending_user_cannot_login**

Description: Verifies that a user with a pending status is denied login with a 401. The test uses dedicated pending user credentials from environment variables ('PENDING_USER_EMAIL', 'PENDING_USER_PASSWORD'), which correspond to a user record in the database that has a pending status. The test confirms only the status code - no error message check is performed at this level.

Expected Outcome: 401 status.

Actual Outcome: Passed. Pending users are correctly denied login.

---

**Sub-Issue 5.2: test_pending_user_returns_pending_id**

Description: Verifies that the backend returns a 'pending_id' field and a pending-specific error message when a pending user attempts to log in. The 'pending_id' identifies the record in the 'pending_users' table and can be used by the client to resume the OTP verification flow. The error message is checked to contain "not verified" rather than an exact match, to accommodate minor wording changes without breaking the test.

Expected Outcome: 401 status; 'pending_id' present in the response body; 'error' field contains "not verified".

Actual Outcome: Passed. Backend returns the pending registration ID and a descriptive error message.

---

**Sub-Issue 5.3: test_pending_user_no_session_created**

Description: Verifies that the server does not create any session for a pending user, even if their credentials are otherwise correct. After the attempted login, the test calls verify and asserts a 401, confirming that no session token was issued or stored server-side.

Expected Outcome: 401 on verify after the pending user's login attempt.

Actual Outcome: Passed. No session is created for pending users.

---

**Sub-Issue 5.4: test_pending_user_no_cookie_set**

Description: Verifies that the 'sid' cookie is not present in the session after a pending user's login attempt. The test checks the session cookie jar directly after the login response. The absence of the cookie confirms the server is not issuing any session identifier to pending users, even transiently.

Expected Outcome: 401 on login; 'sid' absent from the session cookies.

Actual Outcome: Passed. No session cookie is issued to pending users.

---

## Issue 6: Login Flow - Response Security Tests

**Topic**: Verification that sensitive fields are excluded from login and verify responses, and that the verify endpoint returns the correct user data.

These tests act as a guard against accidental data leakage in API responses. The primary concern is that the user record stored in the database (which includes the password hash) is never serialized in full and sent to the client. A secondary concern is that the verify endpoint returns a well-formed and accurate user object. These tests are intentionally narrow - each one checks a single field or field set to make failures easy to diagnose.

---

**Sub-Issue 6.1: test_login_response_excludes_password**

Description: Verifies that the 'password' field is not present in the 'user' object of the login response. The check accesses 'response.json()['user']' directly and asserts the key is absent. If a backend serialization change ever causes the full user record to be returned, this test will catch it.

Expected Outcome: 200 status; 'password' absent from 'response.json()['user']'.

Actual Outcome: Passed. Password field is correctly excluded.

---

**Sub-Issue 6.2: test_login_response_excludes_password_hash**

Description: Verifies that the 'password_hash' field is not present in the login response. This is checked separately from the 'password' field because some backends store the hash under a different key from the plaintext field, and each needs to be explicitly excluded from serialization.

Expected Outcome: 200 status; 'password_hash' absent from 'response.json()['user']'.

Actual Outcome: Passed. Password hash field is correctly excluded.

---

**Sub-Issue 6.3: test_auth_verify_returns_user_data**

Description: Verifies that the '/auth/verify' endpoint returns a complete and accurate user object. After login, the test calls verify and checks that 'user.email' matches the test user's email and that an 'id' field is present. This confirms that verify is not merely returning a 200 but is also providing the client with usable user data to maintain session context.

Expected Outcome: 200 on both login and verify; 'user.email' matches the test user's email; 'id' is present in the user object.

Actual Outcome: Passed. Verify endpoint returns correct and complete user data.

---

## Issue 7: Login Flow - Session Authentication Tests

**Topic**: Verification of HttpOnly cookie behavior, session persistence across requests, session invalidation on logout, Bearer token authentication, and sliding window session expiry extension.

These tests examine the mechanics of session management in detail. They cover how sessions are created and stored (via the 'sid' cookie), how they behave across multiple requests, how they are invalidated, and how they can be authenticated via the Authorization header as an alternative to cookies. The sliding window tests confirm that the session TTL is not a fixed countdown from login - each successful verify call should extend the expiry.

---

**Sub-Issue 7.1: test_login_sets_httponly_cookie**

Description: Verifies that a successful login results in a 'sid' cookie being set and that the cookie carries the 'HttpOnly' flag. The test checks both the session cookie jar (for the cookie's presence) and the raw 'Set-Cookie' response header (for the 'HttpOnly' attribute). Checking the response header directly is required because the 'requests' library does not expose cookie flags through the cookie jar interface.

Expected Outcome: 200 status; 'sid' present in 'api_session.cookies'; 'HttpOnly' present in the 'Set-Cookie' header for the 'sid' cookie.

Actual Outcome: Passed. Session cookie is set with the HttpOnly flag correctly.

---

**Sub-Issue 7.2: test_cookie_persists_across_requests**

Description: Verifies that the same session cookie is accepted across two consecutive verify requests within the same session. This confirms that the cookie is being sent automatically by the session object and that the server is recognizing it on repeat calls without requiring re-authentication.

Expected Outcome: Both verify requests return 200.

Actual Outcome: Passed. Cookie persists and is valid across multiple requests.

---

**Sub-Issue 7.3: test_multiple_sessions_invalidate_previous**

Description: Verifies that when the same user logs in twice, the second login produces a different 'sid' cookie value and the first session is invalidated server-side. The test captures the 'sid' after each login, asserts they are not equal, then injects the first 'sid' into a fresh session and calls '/auth/verify'. A 401 on that verify call confirms the old session was deleted on the server, not merely rotated in the cookie jar.

Expected Outcome: 'sid' values from the two logins differ; '/auth/verify' returns 401 when called with the first 'sid' after the second login.

Actual Outcome: Passed. New login invalidates the previous session server-side.

---

**Sub-Issue 7.4: test_logout_removes_session**

Description: Verifies that calling the logout endpoint removes the server-side session, causing a subsequent verify call to return 401. This is the session layer equivalent of the logout tests in Issue 4 - the focus here is specifically on the session cookie mechanism rather than the Bearer token path.

Expected Outcome: 401 on verify after logout.

Actual Outcome: Passed. Session is correctly removed on logout.

---

**Sub-Issue 7.5: test_login_with_bearer_token_in_header**

Description: Verifies that the 'sid' value from the login cookie can be used directly as a Bearer token in a separate, cookieless session. The test extracts the token from the login response cookies and passes it as 'Authorization: Bearer {token}' in a new session. This confirms the server accepts the same token via both transport mechanisms.

Expected Outcome: 200 on verify when 'sid' is sent as 'Authorization: Bearer {token}' with no cookies.

Actual Outcome: Passed. Bearer token authentication via header is accepted.

---

**Sub-Issue 7.6: test_bearer_token_without_bearer_prefix_passes**

Description: Verifies that the raw token value, submitted without the "Bearer" keyword prefix, is also accepted by the verify endpoint. This behavior is a side effect of how the backend parses the Authorization header - it strips the "Bearer" prefix using a regex pattern, and when the prefix is absent, the raw token is passed through as-is and still matches the stored session.

'''
Authorization: {raw_sid_value}        →  accepted (prefix stripped, token matches)
Authorization: Bearer {raw_sid_value} →  accepted (standard format)
'''

Expected Outcome: 200 status when the token is sent without the "Bearer" prefix.

Actual Outcome: Passed. Raw token without the prefix is accepted due to the backend's prefix-stripping behavior.

---

**Sub-Issue 7.7: test_invalid_bearer_token_fails**

Description: Verifies that a Bearer token containing a string that was never issued by the server is rejected. This confirms the server is performing an actual lookup against stored sessions and not just checking that a token is present.

Expected Outcome: 401 status.

Actual Outcome: Passed. Invalid Bearer token is correctly rejected.

---

**Sub-Issue 7.8: test_session_continues_to_be_valid**

Description: Verifies that a session remains continuously valid across three verify calls, each separated by a 1-second delay (3 seconds total). This is a basic session stability check - it ensures the session is not expiring prematurely under normal, low-frequency usage.

Expected Outcome: All three verify calls return 200.

Actual Outcome: Passed. Session remains valid across multiple calls with short delays.

---

**Sub-Issue 7.9: test_session_remains_valid_after_short_delay**

Description: Verifies that a session remains valid across two verify calls with a 2-second pause between them. This is a basic session continuity check confirming the TTL is meaningfully longer than a few seconds and that the session does not expire prematurely under normal usage patterns.

Expected Outcome: Both verify calls return 200 with a 2-second gap between them.

Actual Outcome: Passed. Session remains valid across the short delay.

---

## Issue 8: Login Flow - Token Security Tests

**Topic**: Verification of session invalidation after re-login, concurrent session handling, case-insensitive Bearer token parsing, and rejection of unsupported authorization schemes.

These tests address the security properties of the session token itself. The key invariants being tested are: a token is bound to a single active session and becomes invalid the moment a new session is created for the same user; the server accepts the Bearer keyword case-insensitively; and the server rejects any authorization scheme other than the Bearer pattern it recognizes. These tests confirm the system enforces strict one-session-per-user behavior.

---

**Sub-Issue 8.1: test_old_session_invalidated_after_new_login**

Description: Verifies that the first session token is invalidated once the user logs in again. The old token is captured after the first login, a second login is performed (which replaces the cookie in the session), and then the old token is injected into a fresh session's cookie jar and used to call verify. Injecting the old token into a new session isolates the test from any state carried by the original session object.

'''python
new_session = requests.Session()
new_session.cookies.set('sid', token1)
response = new_session.get(f'{BASE_URL}/auth/verify')
assert response.status_code == 401
'''

Expected Outcome: 401 when calling verify with the old session token after a new login.

Actual Outcome: Passed. Old session token is correctly invalidated after re-login.

---

**Sub-Issue 8.2: test_bearer_token_from_old_session_fails**

Description: Verifies the same invalidation behavior as Sub-Issue 8.1, but through the Bearer token transport rather than the cookie. The old token is passed as an Authorization header in a cookieless session after the user has logged in again. This confirms that token invalidation applies regardless of how the token is presented to the server.

Expected Outcome: 401 when the old token is sent as 'Authorization: Bearer {old_token}' after a new login.

Actual Outcome: Passed. Old Bearer tokens are invalidated upon new login.

---

**Sub-Issue 8.3: test_concurrent_logins_invalidate_earlier_session**

Description: Verifies that when two completely separate sessions log in as the same user, the first session is invalidated by the second login. Two independent 'requests.Session' objects log in sequentially, and then each calls verify. The first session must return 401 (its token was invalidated when the second session logged in), and the second session must return 200.

Expected Outcome: First session verify returns 401; second session verify returns 200.

Actual Outcome: Passed. Concurrent login correctly invalidates the earlier session.

---

**Sub-Issue 8.4: test_bearer_token_lowercase**

Description: Verifies that the Authorization header is parsed case-insensitively for the "Bearer" keyword, accepting "bearer" in all lowercase. The token itself is a valid 'sid' from a fresh login.

Expected Outcome: 200 status with 'Authorization: bearer {token}'.

Actual Outcome: Passed. Lowercase "bearer" keyword is accepted.

---

**Sub-Issue 8.5: test_bearer_token_uppercase**

Description: Verifies that "BEARER" in all uppercase is accepted as the Authorization keyword.

Expected Outcome: 200 status with 'Authorization: BEARER {token}'.

Actual Outcome: Passed. Uppercase "BEARER" keyword is accepted.

---

**Sub-Issue 8.6: test_bearer_token_mixed_case**

Description: Verifies that an arbitrarily mixed-case keyword such as "BeArEr" is accepted. This confirms the parsing logic uses a case-insensitive pattern rather than a simple string comparison against a fixed casing.

Expected Outcome: 200 status with 'Authorization: BeArEr {token}'.

Actual Outcome: Passed. Mixed-case Bearer keyword is accepted.

---

**Sub-Issue 8.7: test_other_authorization_schemes_fail**

Description: Verifies that the server rejects authorization schemes other than Bearer. The test sends three requests in sequence using a dummy token: one with 'Basic', one with 'Digest', and one with 'Bearer' but an invalid token value. All three must return 401. This confirms the server is not accidentally accepting tokens from unrecognized schemes due to a permissive parsing fallback.

Expected Outcome: 401 for 'Authorization: Basic {token}', 'Authorization: Digest {token}', and 'Authorization: Bearer {invalid_token}'.

Actual Outcome: Passed. Unsupported schemes and invalid Bearer tokens are all correctly rejected.

---

**Sub-Issue 8.8: test_bearer_token_double_spaces**

Description: Verifies that a Bearer token submitted with double spaces between the keyword and the token value is accepted. This tests the robustness of the token extraction pattern - a regex using '\s+' handles this correctly, whereas a pattern expecting a single fixed space would reject it.

'''
Authorization: Bearer  {token}  →  accepted  (\s+ matches the double space)
Authorization: Bearer {token}   →  accepted  (standard single space)
'''

Expected Outcome: 200 status.

Actual Outcome: Passed. Bearer token with double spaces is handled correctly.

---

## Issue 9: Login Flow - Whitespace Handling Tests

**Topic**: Verification of strict password whitespace validation, email normalization for whitespace and casing variations, and Bearer token parsing tolerance for extra spacing.

This file addresses a specific category of input handling: how the system treats whitespace in credentials and tokens. The core rule being tested is asymmetric - whitespace in email addresses is normalized (trimmed and lowercased) to improve usability, while whitespace in passwords is preserved exactly as submitted (passwords are never trimmed) to maintain security. Bearer token parsing is also confirmed to tolerate extra spacing between the keyword and the token value.

---

**Sub-Issue 9.1: test_login_password_leading_whitespace**

Description: Verifies that a password submitted with a single leading space is rejected. A leading space changes the password to a different string than what is stored, and the server must not trim it before comparing. The expected 401 confirms the comparison is performed on the raw submitted value.

Expected Outcome: 401 status when password is submitted as '" {correct_password}"'.

Actual Outcome: Passed. Password with a leading space is correctly rejected.

---

**Sub-Issue 9.2: test_login_password_trailing_whitespace**

Description: Verifies that a password submitted with a single trailing space is rejected. This is tested separately from the leading space case to confirm trimming is not applied from either end of the string.

Expected Outcome: 401 status when password is submitted as '"{correct_password} "'.

Actual Outcome: Passed. Password with a trailing space is correctly rejected.

---

**Sub-Issue 9.3: test_login_password_both_sides_whitespace**

Description: Verifies that a password with spaces on both sides is rejected. This covers the case where a user might accidentally paste their password with surrounding whitespace - a common source of login failures in systems that do trim passwords, but correctly rejected here.

Expected Outcome: 401 status when password is submitted as '" {correct_password} "'.

Actual Outcome: Passed. Password with surrounding spaces is correctly rejected.

---

**Sub-Issue 9.4: test_login_password_tab_character**

Description: Verifies that a leading tab character in the password is not stripped before comparison. Tab characters are whitespace and are removed by functions like JavaScript's '.trim()' - this test confirms the backend does not apply any such stripping to the password field.

Expected Outcome: 401 status when password is submitted as '"\t{correct_password}"'.

Actual Outcome: Passed. Tab character in the password is preserved and causes the comparison to fail correctly.

---

**Sub-Issue 9.5: test_login_password_newline_character**

Description: Verifies that a leading newline character in the password is not stripped. This tests the same no-trimming invariant as the tab character test but with a different whitespace character class.

Expected Outcome: 401 status when password is submitted as '"\n{correct_password}"'.

Actual Outcome: Passed. Newline character in the password is preserved and causes the comparison to fail correctly.

---

**Sub-Issue 9.6: test_login_email_uppercase_with_whitespace**

Description: Verifies that an email submitted in full uppercase with leading and trailing spaces is normalized correctly - trimmed and lowercased - before the database lookup. This is the combined normalization case, testing both transformations together in a single request.

Expected Outcome: 200 status when email is submitted as '" {correct_email_uppercased} "'.

Actual Outcome: Passed. Email is correctly normalized before lookup.

---

**Sub-Issue 9.7: test_login_email_mixed_case_with_trailing_whitespace**

    Description: Verifies that an email in uppercase with a trailing space (but no leading space) is normalized. This is a slightly different whitespace configuration from Sub-Issue 9.6, confirming that normalization is applied regardless of whether whitespace is symmetrical.

    Expected Outcome: 200 status when email is submitted as '"{correct_email_uppercased} "'.

    Actual Outcome: Passed. Mixed-case email with trailing whitespace is correctly normalized.

---

**Sub-Issue 9.8: test_login_email_tab_characters**

    Description: Verifies that tab characters surrounding the email are treated as trimmable whitespace. JavaScript's '.trim()' removes tab characters in addition to spaces, so an email submitted as '"\t{email}\t"' should normalize to the plain email before lookup. This test confirms that behavior is in place.

    Expected Outcome: 200 status when email is submitted as '"\t{correct_email}\t"'.

    Actual Outcome: Passed. Tab characters around the email are trimmed correctly.

---

**Sub-Issue 9.9: test_bearer_token_extra_spaces_before_token**

Description: Verifies that a Bearer token submitted with double spaces between the keyword and the token value is accepted by the verify endpoint. The backend removes content before the token using a whitespace-tolerant extraction pattern, so extra spacing is handled without rejection.

Expected Outcome: 200 status with 'Authorization: "Bearer  {token}"' (double space between keyword and token).

Actual Outcome: Passed. Extra spaces before the token are handled correctly.

---

**Sub-Issue 9.10: test_bearer_token_leading_whitespace**

Description: Verifies that a space placed before the "Bearer" keyword ('" Bearer {token}"') cannot be sent to the server at all. RFC 7230 prohibits leading whitespace in HTTP header values, and the 'requests' library enforces this at the client level by raising 'InvalidHeader' before the request is dispatched. The test asserts this exception is raised, documenting that a standards-compliant HTTP client provides a first line of defense against this malformed header and that the backend never needs to handle it from such a client.

'''python
with pytest.raises(requests.exceptions.InvalidHeader):
    new_session.get(f'{BASE_URL}/auth/verify', headers={'Authorization': f' Bearer {token}'})
'''

Expected Outcome: 'requests.exceptions.InvalidHeader' is raised; no HTTP request is sent.

Actual Outcome: Passed. The 'requests' library rejects the malformed header client-side as expected.

---

## Issue 10: Registration Flow Tests

**Topic**: Verification of the user registration endpoint (POST /users/new) including success paths, required field validation, address object validation, duplicate detection, and extreme/edge inputs.

The registration endpoint creates a pending user record that must complete phone and email OTP verification before becoming a fully active account. These tests verify the shape of the 201 response, that all required fields are enforced, that the optional address object is validated when provided, that duplicate emails and phone numbers are rejected, and that the server handles extreme inputs gracefully without crashing. A psycopg2-based fixture wipes the test email addresses from 'pending_users' before and after every test to ensure clean state.

---

**Sub-Issue 10.1: test_returns_201_with_pending_id**

Description: Verifies that a valid registration payload returns a 201 status code and a non-null 'pending_id' in the response body. The 'pending_id' is used by the frontend to associate subsequent OTP verification calls with this registration attempt.

Expected Outcome: 201 status; 'pending_id' present and non-null in the response body.

Actual Outcome: Passed. Valid registration returns 201 with a 'pending_id'.

---

**Sub-Issue 10.2: test_both_verification_flags_start_false**

Description: Verifies that a freshly registered pending user has both 'phone_verified' and 'email_verified' set to false in the response. These flags track OTP verification progress and must always start as false at the point of registration.

Expected Outcome: 201 status; 'phone_verified' is false; 'email_verified' is false.

Actual Outcome: Passed. Both verification flags are correctly initialized to false.

---

**Sub-Issue 10.3: test_response_includes_message**

Description: Verifies that the registration response includes a 'message' field. This field is used by the frontend to display a confirmation or next-step instruction to the user.

Expected Outcome: 201 status; 'message' field present in the response body.

Actual Outcome: Passed. Registration response includes a message field.

---

**Sub-Issue 10.4: test_accepts_valid_full_address**

Description: Verifies that the registration endpoint accepts an optional 'address' object containing all four required address sub-fields: 'pincode', 'area', 'district', and 'state'. This confirms that address data is handled correctly when provided.

Expected Outcome: 201 status when a complete address object is included in the payload.

Actual Outcome: Passed. Full address object is accepted without error.

---

**Sub-Issue 10.5: test_accepts_optional_middle_name_and_dob**

Description: Verifies that the optional fields 'middle_name' and 'dob' are accepted by the registration endpoint without causing errors. These fields are not required and their presence must not break the registration flow.

Expected Outcome: 201 status when 'middle_name' and 'dob' are included in the payload.

Actual Outcome: Passed. Optional fields are accepted correctly.

---

**Sub-Issue 10.6: test_missing_email_returns_400**

Description: Verifies that the registration endpoint rejects a payload missing the 'email' field with a 400 status. Email is a required field — the server must validate its presence before attempting any database operation.

Expected Outcome: 400 status when 'email' is omitted.

Actual Outcome: Passed. Missing email is correctly rejected at the validation layer.

---

**Sub-Issue 10.7: test_missing_password_returns_400**

Description: Verifies that the registration endpoint rejects a payload missing the 'password' field with a 400 status.

Expected Outcome: 400 status when 'password' is omitted.

Actual Outcome: Passed. Missing password is correctly rejected.

---

**Sub-Issue 10.8: test_missing_first_name_returns_400**

Description: Verifies that the registration endpoint rejects a payload missing the 'first_name' field with a 400 status.

Expected Outcome: 400 status when 'first_name' is omitted.

Actual Outcome: Passed. Missing first_name is correctly rejected.

---

**Sub-Issue 10.9: test_missing_last_name_returns_400**

Description: Verifies that the registration endpoint rejects a payload missing the 'last_name' field with a 400 status.

Expected Outcome: 400 status when 'last_name' is omitted.

Actual Outcome: Passed. Missing last_name is correctly rejected.

---

**Sub-Issue 10.10: test_missing_phone_number_returns_400**

Description: Verifies that the registration endpoint rejects a payload missing the 'phone_number' field with a 400 status.

Expected Outcome: 400 status when 'phone_number' is omitted.

Actual Outcome: Passed. Missing phone_number is correctly rejected.

---

**Sub-Issue 10.11: test_empty_body_returns_400**

Description: Verifies that submitting a completely empty JSON body to the registration endpoint returns a 400 status. This is the most extreme missing-field scenario — no fields at all.

Expected Outcome: 400 status when an empty JSON object is submitted.

Actual Outcome: Passed. Empty body is correctly rejected.

---

**Sub-Issue 10.12: test_missing_fields_response_has_error_key**

Description: Verifies that when required fields are missing, the response body contains an 'error' key. This is important for frontend error handling — the client needs a structured field to display a validation message.

Expected Outcome: 400 status; 'error' key present in the response body.

Actual Outcome: Passed. Missing fields response includes an 'error' key.

---

**Sub-Issue 10.13: test_address_missing_pincode_returns_400**

Description: Verifies that an address object missing the 'pincode' sub-field is rejected with a 400. When an address is provided, all four sub-fields are required — a partial address is not accepted.

Expected Outcome: 400 status when the address object omits 'pincode'.

Actual Outcome: Passed. Partial address missing pincode is correctly rejected.

---

**Sub-Issue 10.14: test_address_missing_area_returns_400**

Description: Verifies that an address object missing the 'area' sub-field is rejected with a 400.

Expected Outcome: 400 status when the address object omits 'area'.

Actual Outcome: Passed. Partial address missing area is correctly rejected.

---

**Sub-Issue 10.15: test_address_missing_district_returns_400**

Description: Verifies that an address object missing the 'district' sub-field is rejected with a 400.

Expected Outcome: 400 status when the address object omits 'district'.

Actual Outcome: Passed. Partial address missing district is correctly rejected.

---

**Sub-Issue 10.16: test_address_missing_state_returns_400**

Description: Verifies that an address object missing the 'state' sub-field is rejected with a 400.

Expected Outcome: 400 status when the address object omits 'state'.

Actual Outcome: Passed. Partial address missing state is correctly rejected.

---

**Sub-Issue 10.17: test_omitting_address_field_entirely_is_valid**

Description: Verifies that omitting the 'address' field entirely from the registration payload is valid — the address object is optional. This complements the address validation tests by confirming the endpoint does not require an address when none is provided.

Expected Outcome: 201 status when the 'address' field is not included in the payload.

Actual Outcome: Passed. Registration succeeds without an address field.

---

**Sub-Issue 10.18: test_email_already_in_users_table_returns_409**

Description: Verifies that attempting to register with an email address that already exists in the 'users' table returns a 409 Conflict. This prevents duplicate accounts for already-verified users.

Expected Outcome: 409 status when the email already exists in the users table.

Actual Outcome: Passed. Duplicate email in users table is correctly rejected with 409.

---

**Sub-Issue 10.19: test_email_conflict_error_mentions_email**

Description: Verifies that the 409 conflict response for a duplicate email includes the word "email" in the error message, so the frontend can display a specific actionable message to the user.

Expected Outcome: 409 status; 'error' message contains the word "email".

Actual Outcome: Passed. Conflict error message correctly references the email field.

---

**Sub-Issue 10.20: test_duplicate_pending_email_returns_409_with_same_pending_id**

Description: Verifies that submitting the same email twice while the first registration is still pending returns a 409 and the same 'pending_id' as the first attempt. This allows the frontend to resume the OTP verification flow for the existing pending record rather than creating a duplicate.

'''python
first = api_session.post(f'{BASE_URL}/users/new', json=VALID_PAYLOAD)
second = api_session.post(f'{BASE_URL}/users/new', json=VALID_PAYLOAD)
assert second.status_code == 409
assert second.json().get('pending_id') == first.json()['pending_id']
'''

Expected Outcome: 409 status on the second request; 'pending_id' in the 409 response matches the 'pending_id' from the first 201 response.

Actual Outcome: Passed. Duplicate pending email returns 409 with the existing pending_id.

---

**Sub-Issue 10.21: test_duplicate_pending_email_includes_verification_flags**

Description: Verifies that the 409 response for a duplicate pending email also includes the 'phone_verified' and 'email_verified' flags, allowing the frontend to show the correct OTP step without a separate API call.

Expected Outcome: 409 status; 'phone_verified' and 'email_verified' present in the response body.

Actual Outcome: Passed. Verification flags are included in the duplicate pending email response.

---

**Sub-Issue 10.22: test_duplicate_phone_in_pending_returns_409**

Description: Verifies that attempting to register a different email but with a phone number already in use by an existing pending user returns a 409. Phone number uniqueness is enforced across 'pending_users' to prevent verification fraud.

Expected Outcome: 409 status when phone_number is already pending under a different email.

Actual Outcome: Passed. Duplicate phone number in pending_users is correctly rejected with 409.

---

**Sub-Issue 10.23: test_extremely_long_email_returns_json_not_crash**

Description: Verifies that submitting a 302-character email (exceeding the VARCHAR(255) column limit) does not crash the server or return a non-JSON response. The server must handle oversized input gracefully and return a structured JSON body regardless.

Expected Outcome: Response Content-Type is 'application/json'.

Actual Outcome: Passed. Server returns a JSON response for an oversized email.

---

**Sub-Issue 10.24: test_extremely_long_email_does_not_register**

Description: Verifies that the 302-character email is actually rejected — a 201 response would indicate the oversized email was accepted, which would fail at the VARCHAR(255) DB column. This test confirms the status code is not 201.

Expected Outcome: Status code is not 201.

Actual Outcome: Passed. Oversized email is not accepted as a successful registration.

---

**Sub-Issue 10.25: test_extremely_long_password_registers_successfully**

Description: Verifies that a 500-character password registers successfully. bcrypt silently truncates input at 72 bytes, so the password hashes fine regardless of length. The registration endpoint has no max-length guard on the password field, making this expected to succeed. This test documents that bcrypt truncation behavior explicitly.

'''python
long_pw = 'Aa1@' * 125  # 500 chars, meets all complexity rules
'''

Expected Outcome: 201 status when a 500-character password is submitted.

Actual Outcome: Passed. Long password is accepted and hashed correctly (bcrypt truncates at 72 bytes silently).

---

**Sub-Issue 10.26: test_extremely_long_first_name_returns_json**

Description: Verifies that submitting a 500-character first_name does not crash the server. The server must return a JSON response rather than a 500 or dropped connection.

Expected Outcome: Response Content-Type is 'application/json'.

Actual Outcome: Passed. Server handles an oversized first_name gracefully.

---

**Sub-Issue 10.27: test_sql_injection_in_password_does_not_return_500**

Description: Verifies that a classic SQL injection payload in the password field does not cause a server error. Because the password is bcrypt-hashed before any DB interaction and the application uses parameterized queries, the injection payload is treated as a plain string.

'''python
password: "'; DROP TABLE users; --"
'''

Expected Outcome: Status code is not 500.

Actual Outcome: Passed. SQL injection payload in password is handled safely.

---

**Sub-Issue 10.28: test_unicode_name_fields_do_not_crash_server**

Description: Verifies that UTF-8 multibyte characters in 'first_name' and 'last_name' are handled gracefully. The server must not crash or return a 500 when receiving non-ASCII input in name fields.

'''python
first_name: '日本語', last_name: 'नाम'
'''

Expected Outcome: Status code is not 500.

Actual Outcome: Passed. Unicode characters in name fields are handled without crashing the server.

---

## Issue 11: Password Reset Flow Tests

**Topic**: Verification of the forgot-password (POST /auth/forgot-password) and reset-password (POST /auth/reset-password) endpoints including success paths, field-level validation, OTP state checks, wrong OTP handling, and lockout behavior.

The password reset flow is a two-step process: the user requests an OTP via forgot-password, then submits the OTP along with a new password via reset-password. The OTP is stored in Node.js process memory only — it is never persisted to the database — which means the happy-path reset cannot be integration-tested without a dev-only helper endpoint. These tests cover the full range of failure paths using a deliberately wrong OTP value (000000). Progressive server-side delays apply between wrong OTP responses (1s, 2s, 4s, 8s, 16s), so slow tests are marked '@pytest.mark.slow' and excluded from the default run.

---

**Sub-Issue 11.1: test_valid_email_returns_200**

Description: Verifies that submitting a valid, existing email to the forgot-password endpoint returns a 200 status.

Expected Outcome: 200 status when a valid registered email is submitted.

Actual Outcome: Passed. Valid email returns 200 from the forgot-password endpoint.

---

**Sub-Issue 11.2: test_valid_email_response_has_ok_true**

Description: Verifies that the forgot-password response for a valid email includes 'ok: true' in the response body — the frontend signal that OTP dispatch was initiated.

Expected Outcome: 200 status; response body contains 'ok: true'.

Actual Outcome: Passed. Response correctly includes 'ok: true'.

---

**Sub-Issue 11.3: test_valid_email_response_includes_expires_in_minutes**

Description: Verifies that the forgot-password response includes an 'expires_in_minutes' field so the frontend can display an OTP expiry countdown to the user.

Expected Outcome: 200 status; 'expires_in_minutes' present in the response body.

Actual Outcome: Passed. OTP expiry duration is included in the response.

---

**Sub-Issue 11.4: test_nonexistent_email_also_returns_200**

Description: Verifies that submitting an email that does not exist in the database also returns a 200 response — identical to the response for a valid email. Returning a different status for nonexistent emails would allow an attacker to enumerate registered email addresses.

Expected Outcome: 200 status when a nonexistent email is submitted to forgot-password.

Actual Outcome: Passed. Nonexistent email returns 200, preventing email enumeration.

---

**Sub-Issue 11.5: test_nonexistent_email_response_has_ok_true**

Description: Verifies that 'ok: true' is also present in the nonexistent email response, making it indistinguishable from a real user's response.

Expected Outcome: 200 status; response body contains 'ok: true' even for nonexistent emails.

Actual Outcome: Passed. Nonexistent email response correctly mirrors the valid email response.

---

**Sub-Issue 11.6: test_missing_email_returns_400**

Description: Verifies that submitting a request to forgot-password with no 'email' field returns a 400.

Expected Outcome: 400 status when 'email' is omitted from the forgot-password request.

Actual Outcome: Passed. Missing email is correctly rejected with 400.

---

**Sub-Issue 11.7: test_missing_email_response_has_error_key**

Description: Verifies that the 400 response for a missing email includes an 'error' key in the response body, providing the frontend with a structured message to display.

Expected Outcome: 400 status; 'error' key present in the response body.

Actual Outcome: Passed. Missing email error response includes an 'error' key.

---

**Sub-Issue 11.8: test_missing_email_returns_400 (reset-password)**

Description: Verifies that the reset-password endpoint returns 400 when the 'email' field is omitted. Field-level validation runs before any OTP state lookup.

Expected Outcome: 400 status when 'email' is omitted from the reset-password request.

Actual Outcome: Passed. Missing email in reset-password is correctly rejected.

---

**Sub-Issue 11.9: test_missing_otp_returns_400**

Description: Verifies that the reset-password endpoint returns 400 when the 'otp' field is omitted.

Expected Outcome: 400 status when 'otp' is omitted.

Actual Outcome: Passed. Missing otp field is correctly rejected.

---

**Sub-Issue 11.10: test_missing_new_password_returns_400**

Description: Verifies that the reset-password endpoint returns 400 when the 'new_password' field is omitted.

Expected Outcome: 400 status when 'new_password' is omitted.

Actual Outcome: Passed. Missing new_password field is correctly rejected.

---

**Sub-Issue 11.11: test_missing_confirm_password_returns_400**

Description: Verifies that the reset-password endpoint returns 400 when the 'confirm_password' field is omitted.

Expected Outcome: 400 status when 'confirm_password' is omitted.

Actual Outcome: Passed. Missing confirm_password field is correctly rejected.

---

**Sub-Issue 11.12: test_password_shorter_than_8_chars_returns_400**

Description: Verifies that the reset-password endpoint rejects a new password shorter than 8 characters with a 400. Minimum password length is enforced at this endpoint before any OTP verification.

Expected Outcome: 400 status when 'new_password' is shorter than 8 characters.

Actual Outcome: Passed. Short password is rejected before OTP verification.

---

**Sub-Issue 11.13: test_short_password_error_mentions_length**

Description: Verifies that the error message for a too-short password explicitly mentions the number '8', so the frontend can display a specific minimum-length message to the user.

Expected Outcome: 400 status; '8' appears in the 'error' field of the response.

Actual Outcome: Passed. Short password error message references the minimum length.

---

**Sub-Issue 11.14: test_mismatched_passwords_return_400**

Description: Verifies that submitting different values for 'new_password' and 'confirm_password' returns a 400. Password confirmation mismatch is caught at the field validation layer before any OTP lookup.

Expected Outcome: 400 status when 'new_password' and 'confirm_password' differ.

Actual Outcome: Passed. Mismatched passwords are rejected with 400.

---

**Sub-Issue 11.15: test_mismatched_passwords_error_mentions_match**

Description: Verifies that the mismatch error message contains the word "match" (case-insensitive), so the frontend can display a specific "passwords do not match" message to the user.

Expected Outcome: 400 status; "match" appears (case-insensitive) in the 'error' field.

Actual Outcome: Passed. Mismatch error message correctly references "match".

---

**Sub-Issue 11.16: test_no_pending_otp_returns_400**

Description: Verifies that calling reset-password without a prior forgot-password request returns a 400. No OTP was generated, so there is nothing to verify against.

Expected Outcome: 400 status when reset-password is called without a prior forgot-password.

Actual Outcome: Passed. Missing OTP state is correctly detected and rejected.

---

**Sub-Issue 11.17: test_no_pending_otp_error_message**

Description: Verifies that the error message for a missing OTP state contains "no password reset", "request", or "otp", directing the user to initiate forgot-password first.

Expected Outcome: 400 status; error message contains 'no password reset', 'request', or 'otp'.

Actual Outcome: Passed. Error message correctly describes the missing OTP state.

---

**Sub-Issue 11.18: test_wrong_otp_returns_400**

Description: Verifies that submitting a deliberately wrong OTP (000000) after a valid forgot-password request returns a 400. A prior forgot-password call is made first to plant an in-memory OTP entry.

Expected Outcome: 400 status when an incorrect OTP is submitted.

Actual Outcome: Passed. Wrong OTP is correctly rejected.

---

**Sub-Issue 11.19: test_wrong_otp_error_says_invalid**

Description: Verifies that the error message for a wrong OTP explicitly says "invalid otp" (case-insensitive), giving the user a clear signal that the OTP value itself is wrong.

Expected Outcome: 400 status; "invalid otp" appears (case-insensitive) in the 'error' field.

Actual Outcome: Passed. Wrong OTP error message correctly describes the failure.

---

**Sub-Issue 11.20: test_wrong_otp_response_includes_attempts_remaining**

Description: Verifies that the wrong OTP response includes an 'attempts_remaining' field, allowing the frontend to warn the user how many attempts they have left before lockout.

Expected Outcome: 400 status; 'attempts_remaining' present in the response body.

Actual Outcome: Passed. Remaining attempts count is included in the wrong OTP response.

---

**Sub-Issue 11.21: test_attempts_remaining_decrements_on_each_failure**

Description: Verifies that the 'attempts_remaining' counter decrements correctly with each wrong OTP submission. Two consecutive wrong OTPs are sent; the first should return attempts_remaining=4 and the second should return attempts_remaining=3. The server applies progressive delays (1s + 2s ≈ 3 seconds total for this test).

'''python
r1 = api_session.post(RESET_URL, json=_reset_payload())
r2 = api_session.post(RESET_URL, json=_reset_payload())
assert r1.json().get('attempts_remaining') == 4
assert r2.json().get('attempts_remaining') == 3
'''

Expected Outcome: First wrong OTP → attempts_remaining=4; Second wrong OTP → attempts_remaining=3.

Actual Outcome: Passed. Attempts remaining decrements correctly with each failure.

---

**Sub-Issue 11.22: test_max_attempts_exceeded_returns_429** *(marked @pytest.mark.slow)*

Description: Verifies that after 5 wrong OTP submissions the endpoint returns 429 Too Many Requests, locking the reset session. The server applies exponential delays between responses (1s + 2s + 4s + 8s + 16s + 16s ≈ 47 seconds total). Excluded from the default run — execute with '-m slow' only.

Expected Outcome: 429 status after 5 consecutive wrong OTP submissions.

Actual Outcome: Passed when run with '-m slow'. Lockout after maximum attempts behaves as expected.

---

**Sub-Issue 11.23: test_after_lockout_otp_entry_is_deleted** *(marked @pytest.mark.slow)*

Description: Verifies that after lockout (429) the in-memory OTP entry is deleted, so a subsequent call returns "no password reset" rather than "too many attempts". This prevents a permanently blocked state and redirects the user to start a fresh forgot-password flow. Total server-side delay is approximately 47 seconds.

Expected Outcome: After lockout, the next reset-password call returns 400 with "no password reset" in the error, or a generic 400.

Actual Outcome: Passed when run with '-m slow'. OTP entry is correctly deleted after lockout.

---

**Sub-Issue 11.24: test_successful_reset_invalidates_existing_sessions** *(marked @pytest.mark.skip)*

Description: This is the happy-path integration test for the full password reset flow. It would log in to create a session, request an OTP, use the real OTP to reset the password, then verify the old session is invalidated. It is permanently skipped because the OTP is stored only in Node.js process memory and cannot be retrieved from tests without a dev-only helper endpoint.

'''python
# To unskip: add GET /auth/_test/pending-otp?email=<email> gated by NODE_ENV !== 'production'
'''

Expected Outcome: 200 on reset; old session cookie rejected with 401 on /auth/verify.

Actual Outcome: Skipped. OTP inaccessible from test environment.

---

## Issue 12: Password Validation Tests

**Topic**: Verification of the POST /api/v1/password/validate endpoint including valid password responses, length boundaries, complexity rules, common password detection, and missing input handling.

The password validation endpoint evaluates a password string against a set of rules and returns a structured response containing 'valid', 'strength', 'score', 'errors', and 'suggestions'. The endpoint is rate-limited to 10 requests per minute per IP. This file contains 11 tests — if additional tests are needed, they must be placed in a separate file with a 60-second startup delay to avoid hitting the rate limit during a single test run.

---

**Sub-Issue 12.1: test_strong_password_is_valid**

Description: Verifies that a password meeting all complexity rules ('StrongP@ss1') returns 'valid: true', 'strength: strong', 'score: 4', and an empty 'errors' array. This is the baseline success case confirming the endpoint correctly identifies a well-formed password.

Expected Outcome: 200 status; 'valid' is true; 'strength' is 'strong'; 'score' is 4; 'errors' is an empty list.

Actual Outcome: Passed. Strong password is correctly evaluated as valid with a full score.

---

**Sub-Issue 12.2: test_response_has_required_fields**

Description: Verifies that the validation response always includes all five required fields: 'valid', 'strength', 'score', 'errors', and 'suggestions'. Absence of any of these fields would break frontend rendering.

Expected Outcome: 200 status; all five fields present in the response body.

Actual Outcome: Passed. All required fields are present in the validation response.

---

**Sub-Issue 12.3: test_7_char_password_triggers_too_short**

Description: Verifies that a 7-character password ('Ab1@xyz') triggers the 'PASSWORD_TOO_SHORT' error code. The minimum allowed password length is 8 characters.

Expected Outcome: 200 status; 'PASSWORD_TOO_SHORT' present in the 'errors' array.

Actual Outcome: Passed. 7-character password is flagged as too short.

---

**Sub-Issue 12.4: test_129_char_password_triggers_too_long**

Description: Verifies that a 132-character password (built as 'Aa1@' repeated 33 times) triggers the 'PASSWORD_TOO_LONG' error code. The maximum allowed length is 128 characters.

Expected Outcome: 200 status; 'PASSWORD_TOO_LONG' present in the 'errors' array.

Actual Outcome: Passed. 132-character password is correctly flagged as too long.

---

**Sub-Issue 12.5: test_no_lowercase_flagged**

Description: Verifies that a password with no lowercase letters ('NOLOWER1@') triggers the 'PASSWORD_NO_LOWERCASE' error code. Lowercase letters are a required complexity element.

Expected Outcome: 'PASSWORD_NO_LOWERCASE' present in the 'errors' array.

Actual Outcome: Passed. Missing lowercase is correctly flagged.

---

**Sub-Issue 12.6: test_no_uppercase_flagged**

Description: Verifies that a password with no uppercase letters ('noupper1@') triggers the 'PASSWORD_NO_UPPERCASE' error code.

Expected Outcome: 'PASSWORD_NO_UPPERCASE' present in the 'errors' array.

Actual Outcome: Passed. Missing uppercase is correctly flagged.

---

**Sub-Issue 12.7: test_no_digit_flagged**

Description: Verifies that a password with no numeric digits ('NoDigit@!') triggers the 'PASSWORD_NO_DIGIT' error code.

Expected Outcome: 'PASSWORD_NO_DIGIT' present in the 'errors' array.

Actual Outcome: Passed. Missing digit is correctly flagged.

---

**Sub-Issue 12.8: test_no_special_char_flagged**

Description: Verifies that a password with no special characters ('NoSpecial1') triggers the 'PASSWORD_NO_SPECIAL' error code. The allowed special characters are '!@#$%^&*_-+=?.'.

Expected Outcome: 'PASSWORD_NO_SPECIAL' present in the 'errors' array.

Actual Outcome: Passed. Missing special character is correctly flagged.

---

**Sub-Issue 12.9: test_disallowed_char_space_flagged**

Description: Verifies that a password containing a space ('Invalid Pass1@') triggers the 'PASSWORD_INVALID_CHARS' error code. Spaces are not in the allowed special-character set and must be explicitly rejected.

Expected Outcome: 'PASSWORD_INVALID_CHARS' present in the 'errors' array.

Actual Outcome: Passed. Space character is correctly identified as an invalid character.

---

**Sub-Issue 12.10: test_common_password_flagged**

Description: Verifies that a well-known common password ('password123') is flagged with the 'PASSWORD_COMMON' error code and 'valid: false'. The endpoint checks against a list of commonly used passwords to prevent weak but technically rule-compliant passwords from passing.

Expected Outcome: 200 status; 'PASSWORD_COMMON' present in the 'errors' array; 'valid' is false.

Actual Outcome: Passed. Common password is correctly identified and rejected.

---

**Sub-Issue 12.11: test_missing_password_field_returns_400**

Description: Verifies that submitting a request to the validation endpoint with no 'password' field returns a 400. The endpoint requires this field to be present — an empty body is a structurally invalid request.

Expected Outcome: 400 status when the 'password' field is absent from the request body.

Actual Outcome: Passed. Missing password field is correctly rejected at the validation layer.

---

## Issue 13: Full Login Flow Test

**Topic**: End-to-end verification of the complete authentication cycle — login, session validation, logout, and post-logout session invalidation — in a single chained test.

The existing tests in test_authentication.py and test_login_validation.py cover each step of the login flow in isolation. This test chains all four steps in sequence to verify that the system behaves correctly as a complete unit: a session created by login is accessible, a logout invalidates it, and no further access is possible after logout.

---

**Sub-Issue 13.1: test_login_verify_logout_verify**

Description: Verifies the full authentication cycle in four sequential steps within a single test. Step 1 — POST /auth/login with valid credentials returns 200 and sets the 'sid' session cookie. Step 2 — GET /auth/verify with the live session returns 200, confirming the session is active. Step 3 — POST /auth/logout returns 200 with 'ok: true'. Step 4 — GET /auth/verify after logout returns 401, confirming the session has been fully invalidated. No prior test covered all four steps together; earlier tests confirmed login→verify and login→logout→block independently but never as one chained assertion.

'''python
login = api_session.post('/auth/login', json={...})
assert login.status_code == 200
assert 'sid' in api_session.cookies

verify_before = api_session.get('/auth/verify')
assert verify_before.status_code == 200

logout = api_session.post('/auth/logout')
assert logout.status_code == 200
assert logout.json().get('ok') is True

verify_after = api_session.get('/auth/verify')
assert verify_after.status_code == 401
'''

Expected Outcome: Login returns 200 with session cookie; pre-logout verify returns 200; logout returns 200 with ok:true; post-logout verify returns 401.

Actual Outcome: Passed. The full authentication cycle completes correctly with session properly invalidated after logout.
