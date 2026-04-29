import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest

class TestHealthCheck:

    @pytest.fixture(scope="module")
    def driver(self):
        driver = webdriver.Chrome()
        yield driver
        driver.quit()

    def test_health_check(self, driver):
        driver.get("http://localhost:5000/api/health") 
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert "ok" in body_text.lower()
    
    def test_health_check_response_format(self, driver):
        driver.get("http://localhost:5000/api/health") 
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert "message" in body_text.lower()   

    