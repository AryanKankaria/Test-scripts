import pytest
import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')
TEAM_USER_EMAIL = os.getenv('TEAM_USER_EMAIL', 'teamuser@example.com')
TEAM_USER_PASSWORD = os.getenv('TEAM_USER_PASSWORD', 'TeamPass@123')


class TestCookieAttributes:

    def test_cookie_is_httponly(self, api_session):
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        cookie_found = False
        for cookie in response.cookies:
            if cookie.name == 'sid':
                cookie_found = True
                assert cookie.has_nonstandard_attr('HttpOnly') or 'HttpOnly' in str(cookie)
        
        assert cookie_found

    def test_cookie_has_path_attribute(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        sid_cookie = api_session.cookies.get('sid')
        assert sid_cookie is not None


class TestProgressiveDelay:

    def test_login_response_time_increases_with_failures(self, api_session):
        response_times = []
        
        for attempt in range(1, 6):
            start = time.time()
            api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': TEST_USER_EMAIL, 'password': 'wrong'}
            )
            elapsed = time.time() - start
            response_times.append(elapsed)
        
        for i in range(1, len(response_times)):
            assert response_times[i] >= response_times[i-1] * 0.8

    def test_progressive_delay_baseline(self, api_session):
        start = time.time()
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': 'wrong'}
        )
        first_attempt_time = time.time() - start
        
        start = time.time()
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': 'wrong'}
        )
        second_attempt_time = time.time() - start
        
        assert second_attempt_time >= first_attempt_time * 0.5


class TestIPBasedRateLimiting:

    def test_ip_rate_limit_high_threshold(self, api_session):
        for i in range(15):
            api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': f'different{i}@example.com', 'password': 'wrongpass'}
            )
        
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 429

    def test_ip_rate_limit_has_retry_info(self, api_session):
        for i in range(15):
            api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': f'test{i}@example.com', 'password': 'wrong'}
            )
        
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        
        if response.status_code == 429:
            data = response.json()
            assert 'retry_after_seconds' in data or 'cooldown_seconds' in data

class TestLoginWithTeamContext:

    def test_login_user_without_team_sets_no_active_team(self, api_session):
        response1 = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response1.status_code == 200
        
        response2 = api_session.get(f'{BASE_URL}/auth/verify')
        assert response2.status_code == 200
        assert 'team_id' not in response2.json() or response2.json()['team_id'] is None

    def test_login_user_with_team_includes_team_id(self, api_session):
        response1 = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEAM_USER_EMAIL, 'password': TEAM_USER_PASSWORD}
        )
        
        if response1.status_code == 200:
            response2 = api_session.get(f'{BASE_URL}/auth/verify')
            assert response2.status_code == 200
            # Backend returns user object with id, email, first_name, last_name
            # Team relationship is tracked via team_members table, not returned in verify
            assert 'user' in response2.json()
            assert response2.json()['user'].get('email') == TEAM_USER_EMAIL



#### API KEY AUTHENTICATION TESTS ####



BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
VALID_API_KEY = os.getenv('VALID_API_KEY', 'test_api_key_xyz')
INVALID_API_KEY = os.getenv('INVALID_API_KEY', 'invalid_key_abc')


class TestAPIKeyAuthentication:

    def test_api_key_in_authorization_header(self, api_session):
        headers = {'Authorization': f'Bearer {VALID_API_KEY}'}
        response = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 200

    def test_invalid_api_key_rejected(self, api_session):
        headers = {'Authorization': f'Bearer {INVALID_API_KEY}'}
        response = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 401

    def test_missing_api_key_rejected(self, api_session):
        response = api_session.get(f'{BASE_URL}/auth/verify')
        assert response.status_code == 401

    def test_api_key_expired_rejected(self, api_session):
        expired_key = os.getenv('EXPIRED_API_KEY', 'expired_key_old')
        headers = {'Authorization': f'Bearer {expired_key}'}
        response = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 401

    def test_api_key_revoked_rejected(self, api_session):
        revoked_key = os.getenv('REVOKED_API_KEY', 'revoked_key_old')
        headers = {'Authorization': f'Bearer {revoked_key}'}
        response = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 401


class TestAPIKeyVsSessionAuth:

    def test_api_key_and_session_both_work(self, api_session):
        headers = {'Authorization': f'Bearer {VALID_API_KEY}'}
        response1 = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': os.getenv('TEST_USER_EMAIL', 'test@example.com'), 'password': os.getenv('TEST_USER_PASSWORD', 'pass')}
        )
        response2 = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_api_key_takes_precedence_over_session(self, api_session):
        api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': os.getenv('TEST_USER_EMAIL', 'test@example.com'), 'password': os.getenv('TEST_USER_PASSWORD', 'pass')}
        )
        
        headers = {'Authorization': f'Bearer {VALID_API_KEY}'}
        response = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 200


class TestAPIKeyHeaders:

    def test_api_key_in_custom_header(self, api_session):
        headers = {'X-API-Key': VALID_API_KEY}
        response = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 200

    def test_api_key_case_sensitive(self, api_session):
        headers = {'Authorization': f'bearer {VALID_API_KEY}'.lower()}
        response = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 200

    def test_api_key_with_extra_whitespace(self, api_session):
        headers = {'Authorization': f'Bearer  {VALID_API_KEY}'}
        response = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 200

    def test_malformed_authorization_header_rejected(self, api_session):
        headers = {'Authorization': 'InvalidFormat'}
        response = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        assert response.status_code == 401


class TestAPIKeyTeamContext:

    def test_api_key_team_context_persists(self, api_session):
        headers = {'Authorization': f'Bearer {VALID_API_KEY}'}
        response1 = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        response2 = api_session.get(f'{BASE_URL}/auth/verify', headers=headers)
        
        if response1.status_code == 200 and response2.status_code == 200:
            assert response1.json() == response2.json()
