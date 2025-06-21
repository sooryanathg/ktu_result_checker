import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()
KTU_USERNAME = os.getenv("KTU_USERNAME")
KTU_PASSWORD = os.getenv("KTU_PASSWORD")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Ask user for semester number (1–8)
while True:
    SEMESTER_ID = input("Enter the semester number to check (1–8): ").strip()
    if SEMESTER_ID.isdigit() and 1 <= int(SEMESTER_ID) <= 8:
        break
    print("⚠️ Please enter a valid semester number between 1 and 8.")


# Setup Edge WebDriver
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
service = Service("msedgedriver.exe")  # Ensure this is in your folder

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, data=data)
    print("Telegram status:", response.status_code)

def check_result():
    driver = webdriver.Edge(service=service, options=options)

    try:
        print("Logging in to KTU portal...")
        driver.get("https://app.ktu.edu.in/login.htm")
        driver.save_screenshot("login_page.png")  # Optional: for debugging

        # ✅ Login using correct element IDs
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "login-username")))
        driver.find_element(By.ID, "login-username").send_keys(KTU_USERNAME)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "login-password")))
        driver.find_element(By.ID, "login-password").send_keys(KTU_PASSWORD)

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btn-login")))
        driver.find_element(By.ID, "btn-login").click()

        time.sleep(4)

        print("Navigating to 'Result' page...")
        driver.get("https://app.ktu.edu.in/eu/res/semesterGradeCardListing.htm")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "semesterGradeCardListingSearchForm_semesterId"))
        )
        semester_dropdown = Select(driver.find_element(By.ID, "semesterGradeCardListingSearchForm_semesterId"))
        print(f"🎯 Selecting Semester S{SEMESTER_ID}...")
semester_dropdown.select_by_value(SEMESTER_ID)


        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "semesterGradeCardListingSearchForm_search"))
        )
        driver.find_element(By.ID, "semesterGradeCardListingSearchForm_search").click()

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table"))
        )
        result_table = driver.find_element(By.CLASS_NAME, "table")
        result_html = result_table.get_attribute("outerHTML")

        result_html = result_table.get_attribute("outerHTML")

        # ✅ Show result content in readable text format
        print("\n📋 Latest Semester Result:")
        print(result_table.text)  # This prints the entire result table cleanly

        driver.save_screenshot("result_page.png")  # Optional

        # First time: create last_result.txt
        if not os.path.exists("last_result.txt"):
            with open("last_result.txt", "w", encoding="utf-8") as f:
                f.write(result_html)

        with open("last_result.txt", "r", encoding="utf-8") as f:
            previous_html = f.read()

        if result_html != previous_html:
            print("New result found! Sending alert...")
            send_telegram("🎉 Your KTU Semester 3 result is now available!")
            with open("last_result.txt", "w", encoding="utf-8") as f:
                f.write(result_html)
        else:
            print("No change in result. Checked successfully.")


    except Exception as e:
        print(f"Error: {e}")
        send_telegram(f"Error while checking result: {e}")
        driver.save_screenshot("error_page.png")  # Helps with debugging

    finally:
        driver.quit()

# Run every hour
while True:
    check_result()
    time.sleep(3600)
