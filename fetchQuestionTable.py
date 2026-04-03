import os
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


CSV_FILE = "DAA_ CodechefContests.csv"
OUTPUT_DIR = "data"

import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def fetch_and_save_table(driver, contest_code, output_dir="data", timeout=10):
    """
    Extract table inside contestProblems div and save as HTML
    """

    url = f"https://www.codechef.com/manage/{contest_code}?tab=contest_problems"
    print(f"\n➡ Processing {contest_code}")

    driver.get(url)

    wait = WebDriverWait(driver, timeout)

    try:
        # 🔹 Step 1: find the parent div (robust match)
        parent_div = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[class*='contestProblems']")
            )
        )

        # 🔹 Step 2: find table INSIDE that div
        table = parent_div.find_element(By.TAG_NAME, "table")

        html = table.get_attribute("outerHTML")

        # 📁 Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, f"{contest_code}.html")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✅ Saved: {file_path}")
        return True

    except Exception as e:
        print(f"❌ Failed for {contest_code}: {e}")
        return False

# ✅ Read first N contest codes
def read_contest_codes(csv_file, limit=3):
    codes = []

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            code = row.get("Assessment Code", "").strip()
            if code:
                codes.append(code)

            if len(codes) >= limit:
                break

    return codes


def main():
    # 📁 Create data directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 🔹 Setup Chrome
    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    try:
        # 🔐 Manual login
        driver.get("https://www.codechef.com/login")
        input("Login manually, then press ENTER...")

        # 📥 Read contest codes (first 3)
        contest_codes = read_contest_codes(CSV_FILE, limit=3)

        print("Processing contests:", contest_codes)

        for code in contest_codes:
        	fetch_and_save_table(driver, code)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
