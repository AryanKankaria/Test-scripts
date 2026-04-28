import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

@pytest.fixture
def login_page(driver):
    html_path = Path(__file__).parent / "index.html"    
    driver.get(f"file:///{html_path.absolute()}")
    return driver

class TestLoginPageElements:
    def test_username_field_exists(self, login_page):
        username = login_page.find_element(By.ID, "username")
        assert username is not None
        assert username.get_attribute("type") == "text"

    def test_password_field_exists(self, login_page):
        password = login_page.find_element(By.ID, "password")
        assert password is not None
        assert password.get_attribute("type") == "password"

    def test_login_button_exists(self, login_page):
        button = login_page.find_element(By.ID, "login-btn")
        assert button is not None
        assert button.text == "Sign in"

    def test_remember_checkbox_exists(self, login_page):
        checkbox = login_page.find_element(By.ID, "remember")
        assert checkbox is not None
        assert checkbox.get_attribute("type") == "checkbox"

    def test_error_message_div_exists(self, login_page):
        error = login_page.find_element(By.ID, "error-msg")
        assert error is not None

    def test_success_message_div_exists(self, login_page):
        success = login_page.find_element(By.ID, "success-msg")
        assert success is not None

class TestLoginFunctionality:
    def test_login_with_correct_credentials(self, login_page):
        login_page.find_element(By.ID, "username").send_keys("admin")
        login_page.find_element(By.ID, "password").send_keys("password123")
        login_page.find_element(By.ID, "login-btn").click()

        success = WebDriverWait(login_page, 5).until(
            EC.visibility_of_element_located((By.ID, "success-msg"))
        )
        assert "Login successful" in success.text

    def test_login_with_wrong_credentials(self, login_page):
        login_page.find_element(By.ID, "username").send_keys("admin")
        login_page.find_element(By.ID, "password").send_keys("wrongpass")
        login_page.find_element(By.ID, "login-btn").click()

        error = WebDriverWait(login_page, 5).until(
            EC.visibility_of_element_located((By.ID, "error-msg"))
        )
        assert "Invalid username or password" in error.text

    def test_login_with_empty_fields(self, login_page):
        login_page.find_element(By.ID, "login-btn").click()

        error = WebDriverWait(login_page, 5).until(
            EC.visibility_of_element_located((By.ID, "error-msg"))
        )
        assert "Please fill in all fields" in error.text

    def test_login_with_empty_password(self, login_page):
        login_page.find_element(By.ID, "username").send_keys("admin")
        login_page.find_element(By.ID, "login-btn").click()

        error = WebDriverWait(login_page, 5).until(
            EC.visibility_of_element_located((By.ID, "error-msg"))
        )
        assert "Please fill in all fields" in error.text

    def test_enter_key_submits_form(self, login_page):
        login_page.find_element(By.ID, "username").send_keys("admin")
        password_field = login_page.find_element(By.ID, "password")
        password_field.send_keys("password123")
        password_field.send_keys("\n")  # Simulate Enter key

        success = WebDriverWait(login_page, 5).until(
            EC.visibility_of_element_located((By.ID, "success-msg"))
        )
        assert "Login successful" in success.text