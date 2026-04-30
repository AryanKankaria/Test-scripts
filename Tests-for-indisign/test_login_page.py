import pytest
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

load_dotenv()

APP_URL = os.getenv('APP_URL', 'http://localhost:3001')
TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'testuser@example.com')
TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'TestPassword@123')


@pytest.fixture
def driver():
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0')
    
    driver = webdriver.Chrome(options=chrome_options)
    yield driver
    driver.quit()


class TestLoginPageUI:

    def test_login_page_loads(self, driver):
        driver.get(f'{APP_URL}/login')
        assert 'login' in driver.title.lower() or 'sign in' in driver.title.lower()

    def test_login_form_has_email_input(self, driver):
        driver.get(f'{APP_URL}/login')
        wait = WebDriverWait(driver, 10)
        email_field = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        assert email_field is not None

    def test_login_form_has_password_input(self, driver):
        driver.get(f'{APP_URL}/login')
        wait = WebDriverWait(driver, 10)
        password_field = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        assert password_field is not None

    def test_login_form_has_submit_button(self, driver):
        driver.get(f'{APP_URL}/login')
        wait = WebDriverWait(driver, 10)
        button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@type='submit']")))
        assert button is not None


class TestLoginPageUISubmission:

    def test_login_with_valid_credentials(self, driver):
        driver.get(f'{APP_URL}/login')
        wait = WebDriverWait(driver, 10)
        
        email_field = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        password_field = driver.find_element(By.NAME, 'password')
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        
        email_field.send_keys(TEST_USER_EMAIL)
        password_field.send_keys(TEST_USER_PASSWORD)
        submit_button.click()
        
        wait.until(EC.url_changes(driver.current_url))
        assert 'login' not in driver.current_url.lower()

    def test_login_with_invalid_password(self, driver):
        driver.get(f'{APP_URL}/login')
        wait = WebDriverWait(driver, 10)
        
        email_field = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        password_field = driver.find_element(By.NAME, 'password')
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        
        email_field.send_keys(TEST_USER_EMAIL)
        password_field.send_keys('WrongPassword123')
        submit_button.click()
        
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'invalid') or contains(text(), 'error')]")))
        assert 'login' in driver.current_url.lower()

    def test_login_shows_error_with_empty_email(self, driver):
        driver.get(f'{APP_URL}/login')
        wait = WebDriverWait(driver, 10)
        
        password_field = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        
        password_field.send_keys(TEST_USER_PASSWORD)
        submit_button.click()
        
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'required') or contains(text(), 'email')]")))
        assert 'login' in driver.current_url.lower()

    def test_login_shows_error_with_empty_password(self, driver):
        driver.get(f'{APP_URL}/login')
        wait = WebDriverWait(driver, 10)
        
        email_field = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        
        email_field.send_keys(TEST_USER_EMAIL)
        submit_button.click()
        
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'required') or contains(text(), 'password')]")))
        assert 'login' in driver.current_url.lower()

    def test_logout_redirects_to_login(self, driver):
        driver.get(f'{APP_URL}/login')
        wait = WebDriverWait(driver, 10)
        
        email_field = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        password_field = driver.find_element(By.NAME, 'password')
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        
        email_field.send_keys(TEST_USER_EMAIL)
        password_field.send_keys(TEST_USER_PASSWORD)
        submit_button.click()
        
        wait.until(EC.url_changes(driver.current_url))
        
        logout_link = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@class*='logout' or contains(text(), 'logout') or contains(text(), 'Logout')]")))
        logout_link.click()
        
        wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        assert 'login' in driver.current_url.lower()

    def test_protected_page_redirects_to_login_without_session(self, driver):
        driver.get(f'{APP_URL}/dashboard')
        wait = WebDriverWait(driver, 10)
        
        wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        assert 'login' in driver.current_url.lower()
