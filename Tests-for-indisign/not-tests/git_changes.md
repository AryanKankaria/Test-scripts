# Git Changes — Removed Sub-Issues

Date: May 8, 2026
Reason: Deduplication audit. All tests below were either exact duplicates of tests
in other files, merged into a single stronger test, or not testing backend behaviour.

---

**2.3 — test_login_removes_previous_sessions**
Removed. Identical logic to 7.3 (test_multiple_sessions_invalidate_previous in
test_session_auth.py). Both log in twice, assert the SID changed, inject the old SID
into a fresh session, and assert 401. 7.3 is kept as it also asserts login status codes.

---

**2.10 — test_rate_limit_returns_retry_after**
Removed. Merged into 2.9 (test_rate_limit_after_failed_attempts). Both made 11 failed
attempts and asserted 429. The only difference was which response field each checked
('cooldown'/'retry' text vs. 'retry_after_seconds'/'cooldown_seconds' JSON key). The
merged 2.9 now asserts both the 'error' key and the timing field in one test.

---

**2.12 — test_logout_invalidates_cookie**
Removed. Identical to 4.4 (test_logout_invalidates_session_cookie in
test_logout_advanced.py). Both log in, call logout, then call verify and assert 401.
4.4 is kept as it also asserts the session was valid before logout.

---

**2.15 — test_request_with_authorization_header**
Removed. Identical to 7.5 (test_login_with_bearer_token_in_header in
test_session_auth.py). Both extract the sid cookie after login and use it as a Bearer
token in a separate cookieless session to call verify, asserting 200.

---

**2.16 — test_session_remains_valid_after_short_delay**
Removed. Exact duplicate of 7.9 (same function name and logic in test_session_auth.py).
Both log in, call verify, sleep 2 seconds, call verify again, and assert 200 both times.

---

**2.17 — test_invalid_token_format**
Removed. Identical to 7.7 (test_invalid_bearer_token_fails in test_session_auth.py).
Both send a Bearer token with a fabricated string value and assert 401.

---

**3.8 — test_multiple_failed_logins_increase_cooldown**
Originally removed as a duplicate of the merged 2.9 — it only checked that 429 was
returned, not that the cooldown actually grew.

Re-added May 8, 2026 in corrected form. The test now makes 11 failures to reach the
threshold, captures the cooldown value from the first 429, makes one further failed
attempt, and asserts the second cooldown value is greater than or equal to the first.
This test specifically verifies the cooldown VALUE grows within a single continuous session.

---

**3.9 — test_rate_limit_response_contains_retry_info**
Removed. Duplicate of the merged 2.9. Same 11-attempt setup, same 429 assertion, same
'error' and timing field checks. Indistinguishable from 2.9 in what it exercises.

---

**3.10 — test_password_is_required**
Removed. Identical to 2.7 (test_login_missing_password in test_authentication.py).
Both send a request with only the email field present and assert 400.

---

**3.11 — test_email_is_required**
Removed. Identical to 2.6 (test_login_missing_email in test_authentication.py).
Both send a request with only the password field present and assert 400.

---

**3.14 — test_empty_string_credentials_rejected**
Removed. Identical to 2.8 (test_login_empty_credentials in test_authentication.py).
Both send {'email': '', 'password': ''} and assert 400.

---

**3.15 — test_successful_login_user_can_access_protected_endpoint**
Removed. Duplicate of 2.2 (test_login_creates_valid_session in test_authentication.py).
Both log in and call verify, asserting 200 and the presence of user data in the response.

---

**3.17 — test_after_logout_user_cannot_access_protected_endpoint**
Removed. Identical to 4.4 (test_logout_invalidates_session_cookie in
test_logout_advanced.py). Both log in, call logout, call verify, and assert 401.

---

**7.4 — test_logout_removes_session**
Removed. Identical to 4.4 (test_logout_invalidates_session_cookie in
test_logout_advanced.py). Both log in, call logout, call verify, and assert 401.

---

**8.1 — test_old_session_invalidated_after_new_login**
Removed. Identical to 7.3 (test_multiple_sessions_invalidate_previous in
test_session_auth.py). Both log in twice using the same session, then inject the first
token into a new session and assert verify returns 401. 7.3 is kept as it additionally
asserts the two SID values differ.

---

**8.4 — test_bearer_token_lowercase**
**8.5 — test_bearer_token_uppercase**
**8.6 — test_bearer_token_mixed_case**
Consolidated. All three were separate test functions that exercised the same code path
(Bearer keyword parsing) with only the keyword casing differing ('bearer', 'BEARER',
'BeArEr'). Replaced with a single parameterized test
(test_bearer_keyword_is_case_insensitive) that runs all three cases. Test case count
is unchanged — still three cases, one function.

---

**9.9 — test_bearer_token_extra_spaces_before_token**
Removed. Identical to 8.8 (test_bearer_token_double_spaces in test_token_security.py).
Both send 'Authorization: Bearer  {token}' (double space) and assert 200.

---

**9.10 — test_bearer_token_leading_whitespace**
Originally removed. The test used 'requests', which enforces RFC 7230 header value
restrictions client-side by raising InvalidHeader — the server was never reached, so
no backend behaviour was being verified.

Re-added May 8, 2026 in corrected form. The test now uses Python's built-in
'http.client', which does not enforce RFC 7230 header value restrictions and sends
the leading-space header directly to the server. The assertion checks that the backend
returns 400 or 401, confirming it does not accidentally accept a malformed Authorization
header as valid.
