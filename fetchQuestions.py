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


CSV_FILE = "grouped_problems.csv"
OUTPUT_DIR = "problems"

BASE_URL = "https://www.codechef.com/THADAA/problems/{}"
MAX_DOWNLOADS = 10     #+ve to fix limit; -1 to download all


OUTPUT_HTML_DIR = "problems/html"
OUTPUT_PDF_DIR = "problems/pdf"

os.makedirs(OUTPUT_HTML_DIR, exist_ok=True)
os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)

def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")  # adjust path

    driver = webdriver.Chrome(service=service, options=options)
    return driver


def wait_for_manual_login(driver):
    driver.get("https://www.codechef.com/")
    print("\n🔐 Login manually...")
    input("👉 Press ENTER after login...")


def read_problem_ids():
    problem_ids = set()

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")

        next(reader)  # 🔥 skip header row

        for row in reader:
            # skip first column (ContestCode)
            for value in row[1:]:
                if value and value.strip():
                    problem_ids.add(value.strip())

    return sorted(problem_ids)

import os
import time
import base64
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OUTPUT_HTML_DIR = "problems/html"
OUTPUT_PDF_DIR = "problems/pdf"

os.makedirs(OUTPUT_HTML_DIR, exist_ok=True)
os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)


def save_problem(driver, pid):
    try:
        print(f"Processing {pid}")

        url = f"https://www.codechef.com/THADAA/problems/{pid}"
        driver.get(url)

        # wait for problem statement
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "problem-statement"))
        )

        time.sleep(2)  # allow full render

        # 🔥 Extract HTML
        element = driver.find_element(By.ID, "problem-statement")
        html_content = element.get_attribute("outerHTML")

        # ✅ Save HTML
        html_path = os.path.join(OUTPUT_HTML_DIR, f"{pid}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 🔥 Inject clean styling for PDF
        driver.execute_script("""
            var style = document.createElement('style');
            style.innerHTML = `
                * {
                    background: white !important;
                    color: black !important;
                }
                pre, code {
                    background: #f5f5f5 !important;
                }
            `;
            document.head.appendChild(style);
        """)

        time.sleep(1)

        # ✅ Generate PDF
        pdf = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True
        })

        pdf_path = os.path.join(OUTPUT_PDF_DIR, f"{pid}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(base64.b64decode(pdf['data']))

        print(f"Saved HTML + PDF for {pid}")

    except Exception as e:
        print(f"Error for {pid}: {e}")

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

    problem_ids = read_problem_ids()
    print("Problems:",problem_ids)

    count = 0

    for pid in problem_ids:
        if MAX_DOWNLOADS != -1 and count >= MAX_DOWNLOADS:
            print("Download limit reached")
            break
            
        try:
            #save_pdf(driver, pid)
            save_problem(driver, pid)
            count += 1

        except Exception as e:
            print(f"⚠ Unexpected error: {e}")

            # 🔥 Restart browser if crash
            try:
                driver.quit()
            except:
                pass

            driver = setup_driver()
            wait_for_manual_login(driver)

        time.sleep(2)

    driver.quit()

    print(f"\n🎯 Total downloaded: {count}")


if __name__ == "__main__":
    main()