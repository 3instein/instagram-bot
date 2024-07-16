from flask import Flask, request, jsonify
import time
import random
import pickle
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Function to log time taken by functions
def log_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        app.logger.info(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper

# Function to save cookies
def save_cookies(driver, path):
    with open(path, 'wb') as file:
        pickle.dump(driver.get_cookies(), file)

# Function to load cookies
def load_cookies(driver, path):
    with open(path, 'rb') as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)

# Function for Instagram login
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
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))

        username_field = driver.find_element(By.NAME, "username")
        username_field.send_keys(username)

        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[text()='Direct']")))
        save_cookies(driver, cookie_path)
        driver.get("https://www.instagram.com/direct/")

    return driver

# Function to send OTP
@log_time
def send_otp(driver, recipient_username, otp):
    try:
        turn_off_notifications_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']")))
        turn_off_notifications_button.click()
    except:
        pass

    try:
        send_message_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[text()='Send message']")))
        send_message_button.click()
    except:
        pass

    query_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "queryBox")))
    query_box.send_keys(recipient_username)

    contact_search_result_checkbox = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "ContactSearchResultCheckbox")))
    contact_search_result_checkbox.click()

    chat_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Chat']")))
    chat_button.click()

    message_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, "//div[@aria-describedby='Message']")))
    message_box.click()
    message_box.send_keys(f"Your OTP is: {otp}")
    message_box.send_keys(Keys.RETURN)

    time.sleep(1)

# Function to generate OTP
def generate_otp(length=6):
    return ''.join(random.choices('0123456789', k=length))

# API route for logging in and sending OTP
@app.route('/send-otp', methods=['POST'])
def api_send_otp():
    req_data = request.get_json()

    with open("secrets.txt") as file:
        username = file.readline().strip()
        password = file.readline().strip()
    username = req_data.get('username')

    otp = generate_otp()

    driver = instagram_login(username, password)
    send_otp(driver, username, otp)
    driver.quit()

    response = {
        "message": "OTP sent successfully!",
        "otp": otp
    }

    return jsonify(response)

# API Route for checking instagram post link
@app.route('/validate', methods=['POST'])
def api_check_link():
    req_data = request.get_json()
    link = req_data.get('link')

    options = Options()
    options.headless = True

    driver = webdriver.Chrome(options=options)
    driver.get(link)

    # find span with text Sorry, this page isn't available.
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[text()='Sorry, this page isn't available.']")))
        response = {
            "message": "Post does not exist!"
        }
    except:
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h1")))
            caption = driver.find_element(By.XPATH, "//h1")

            #find span with style line-height: var(--base-line-clamp-line-height); --base-line-clamp-line-height: 18px;
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[@style='line-height: var(--base-line-clamp-line-height); --base-line-clamp-line-height: 18px;']")))
            username = driver.find_element(By.XPATH, "//span[@style='line-height: var(--base-line-clamp-line-height); --base-line-clamp-line-height: 18px;']")

            response = {
                "message": "Post exists!",
                "username": username.text,
                "caption": caption.text
            }
        except:
            pass

    driver.quit()

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)