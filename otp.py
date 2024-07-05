import time
import random
import pickle
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logging.basicConfig(level=logging.INFO, filename='performance.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')


def log_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(
            f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper


def save_cookies(driver, path):
    with open(path, 'wb') as file:
        pickle.dump(driver.get_cookies(), file)


def load_cookies(driver, path):
    with open(path, 'rb') as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)


@log_time
def instagram_login(username, password, cookie_path="cookies.pkl"):
    options = Options()
    options.headless = True  # Run in headless mode
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.instagram.com/direct")

    if os.path.exists(cookie_path):
        load_cookies(driver, cookie_path)
        driver.refresh()
    else:
        driver.get("https://www.instagram.com/accounts/login/")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username")))

        username_field = driver.find_element(By.NAME, "username")
        username_field.send_keys(username)

        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[text()='Direct']")))
        save_cookies(driver, cookie_path)
        driver.get("https://www.instagram.com/direct/")

    return driver


@log_time
def send_otp(driver, recipient_username, otp):
    try:
        turn_off_notifications_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']")))
        turn_off_notifications_button.click()
    except Exception as e:
        logging.warning(f"Failed to turn off notifications: {e}")

    try:
        send_message_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[text()='Send message']")))
        send_message_button.click()
    except Exception as e:
        logging.warning(f"Failed to find/send message button: {e}")

    try:
        query_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.NAME, "queryBox")))
        query_box.send_keys(recipient_username)

        contact_search_result_checkbox = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.NAME, "ContactSearchResultCheckbox")))
        contact_search_result_checkbox.click()

        chat_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[text()='Chat']")))
        chat_button.click()

        message_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-describedby='Message']")))
        message_box.click()
        message_box.send_keys(f"Your OTP is: {otp}")
        message_box.send_keys(Keys.RETURN)
    except Exception as e:
        logging.error(f"Failed to send OTP: {e}")


def generate_otp(length=6):
    return ''.join(random.choices('0123456789', k=length))


@log_time
def main():
    with open("secrets.txt") as file:
        username = file.readline().strip()
        password = file.readline().strip()
    recipient_username = "reynaldi_kindarto"

    otp = generate_otp()
    print(f"Generated OTP: {otp}")

    driver = instagram_login(username, password)
    send_otp(driver, recipient_username, otp)

    driver.quit()


if __name__ == "__main__":
    main()