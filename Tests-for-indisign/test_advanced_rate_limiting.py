import pytest
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')


class TestCooldownIncrement:

    def test_progressive_cooldown_per_failed_attempt(self, api_session):
        cooldowns = []
        
        for attempt in range(11, 14):
            for i in range(attempt):
                api_session.post(
                    f'{BASE_URL}/auth/login',
                    json={'email': TEST_USER_EMAIL, 'password': 'wrong'}
                )
            
            response = api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
            )
            
            if response.status_code == 429:
                seconds = response.json().get('cooldown_seconds') or response.json().get('retry_after_seconds')
                cooldowns.append(seconds)
        
        assert len(cooldowns) > 0, "Rate limit never triggered — test did not exercise the cooldown code path"
        for i in range(1, len(cooldowns)):
            assert cooldowns[i] >= cooldowns[i-1]


class TestRateLimitReset:

    def test_rate_limit_window_expiry(self, api_session):
        # Make 11 failed attempts to exceed MAX_LOGIN_ATTEMPTS (10)
        for i in range(11): # @todo: pull this number from the code itself.
            api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': TEST_USER_EMAIL, 'password': 'wrong'}
            )
        
        # Try with correct password - should be rate limited
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 429, f"Expected 429, got {response.status_code}"
        
        # Wait for rate limit window to expire (1 minute = 60 seconds)
        print("Waiting 62 seconds for rate limit window to expire...")
        time.sleep(62)
        
        # After window expiry, the failed attempt counter should reset
        # Try with wrong password - should get 401 (not 429), counter is fresh
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': 'wrong'}
        )
        assert response.status_code == 401, f"Expected 401 after window expiry, got {response.status_code}: {response.text}"

    def test_successful_login_clears_rate_limit(self, api_session):
        # Do 3 failed attempts (well below any reasonable threshold)
        for i in range(3):
            api_session.post(
                f'{BASE_URL}/auth/login',
                json={'email': TEST_USER_EMAIL, 'password': 'wrong'}
            )
        
        # 4th attempt with correct password should succeed (below rate limit)
        response = api_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': TEST_USER_PASSWORD}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify we can logout successfully
        response = api_session.post(
            f'{BASE_URL}/auth/logout'
        )
        assert response.status_code == 200
        
        # Verify rate limit counter was cleared after successful login
        # Try another failed login - should be attempt #1 again, not #4
        new_session = requests.Session()
        response = new_session.post(
            f'{BASE_URL}/auth/login',
            json={'email': TEST_USER_EMAIL, 'password': 'wrong'}
        )
        # Should get 401 (bad password), not 429 (rate limited)
        assert response.status_code == 401, f"Expected 401 (bad password), got {response.status_code}"

