import csv
import os
import time
import base64

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

CSV_FILE = "grouped_problems.csv"
OUTPUT_DIR = "problems"

BASE_URL = "https://www.codechef.com/THADAA/problems/{}"
MAX_DOWNLOADS = 10

def setup_driver():
    options = Options()
    options.add_argument("--user-data-dir=/home/YOUR_USER/.config/google-chrome")
    options.add_argument("--profile-directory=Default")  # or Profile 1
    options.add_argument("--start-maximized")
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def wait_for_manual_login(driver):
    driver.get("https://www.codechef.com/")
    print("\n🔐 Login manually...")
    input("👉 Press ENTER after login...")


def read_problem_ids():
    problem_ids = set()  # 🔥 deduplicate

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            for key in row:
                if key.startswith("P") and row[key].strip():
                    problem_ids.add(row[key].strip())

    return list(problem_ids)


def save_pdf(driver, problem_id):
    try:
        url = BASE_URL.format(problem_id)
        print(f"➡ {problem_id}")

        driver.get(url)

        # 🔹 Wait for problem statement
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "problem-statement"))
        )

        # 🔹 Keep only problem content
        driver.execute_script("""
        document.body.innerHTML =
        document.getElementById('problem-statement').outerHTML;
        """)

        time.sleep(1)

        # 🔹 Generate PDF
        pdf = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True
        })

        file_path = os.path.join(
            OUTPUT_DIR, f"{problem_id}.pdf"
        )

        with open(file_path, "wb") as f:
            f.write(base64.b64decode(pdf['data']))

        print(f"✅ Saved {problem_id}.pdf")

    except Exception as e:
        print(f"❌ Failed {problem_id}: {e}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    driver = setup_driver()
    wait_for_manual_login(driver)
    driver.quit()

    print(f"\n🎯 Total downloaded: {count}")


if __name__ == "__main__":
    main()
