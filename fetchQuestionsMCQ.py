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


CSV_FILE = "grouped_MCQ.tsv"
OUTPUT_DIR = "contest/MCQ"

#BASE_URL = "https://www.codechef.com/THADAA/problems/{}" # Provided by Codechef 
BASE_URL="https://www.codechef.com/learn/course/user/I5P77/problems/{}" # Provided by Codechef 
MAX_DOWNLOADS = -1     #+ve to fix limit; -1 to download all


OUTPUT_HTML_DIR = OUTPUT_DIR+"/html"
OUTPUT_PDF_DIR = OUTPUT_DIR+"/pdf"
FAILED_TO_DOWNLOAD=[]

os.makedirs(OUTPUT_HTML_DIR, exist_ok=True)
os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)

import argparse

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--only-new",
        action="store_true",
        help="Download only problems not already downloaded"
    )
    parser.add_argument(
        "--mcq",
        action="store_true",
        help="Download MCQs also"
    )

    return parser.parse_args()


def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")  # adjust path

    driver = webdriver.Chrome(service=service, options=options)
    return driver

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64

def save_page_as_pdf(driver, pid, DOWNLOAD_ONLY_NEW):
    try:
        html_path = os.path.join(OUTPUT_HTML_DIR, f"{problem_id}.html")
        pdf_path = os.path.join(OUTPUT_PDF_DIR, f"{problem_id}.pdf")
        # 🔥 Skip if already downloaded
        if only_new and os.path.exists(html_path) and os.path.exists(pdf_path):
            print(f"⏭ Skipping {problem_id} (already exists)")
            return

        url = BASE_URL.format(problem_id)
        print(f"➡ {problem_id}")
        driver.get(url)

        # Optional: wait for page to fully load
        driver.implicitly_wait(5)

        # Use Chrome DevTools Protocol to print as PDF
        pdf = driver.execute_cdp_cmd(
            "Page.printToPDF",
            {
                "printBackground": True,
                "paperWidth": 8.27,   # A4 width in inches
                "paperHeight": 11.69, # A4 height in inches
                "marginTop": 0.4,
                "marginBottom": 0.4,
                "marginLeft": 0.4,
                "marginRight": 0.4,
            },
        )

        with open(output_path, "wb") as f:
            f.write(base64.b64decode(pdf['data']))

        print(f"Saved PDF to {output_path}")

    finally:
        driver.quit()


def wait_for_manual_login(driver):
    driver.get("https://www.codechef.com/")
    print("\n🔐 Login manually...")
    input("👉 Press ENTER after login...")


def read_problem_ids(DOWNLOAD_MCQ):
    problem_ids = set()

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")

        next(reader)  # 🔥 skip header row
        for row in reader:
            # skip first column (ContestCode)
            for value in row[1:]:
                if value and value.strip():
                    if value.strip().startswith("THAPARMCQ"):
                            continue
                    else:
                        problem_ids.add(value.strip())

    return sorted(problem_ids)

def save_problem(driver, problem_id, only_new=False):
    try:
        html_path = os.path.join(OUTPUT_HTML_DIR, f"{problem_id}.html")
        pdf_path = os.path.join(OUTPUT_PDF_DIR, f"{problem_id}.pdf")

        # 🔥 Skip if already downloaded
        if only_new and os.path.exists(html_path) and os.path.exists(pdf_path):
            print(f"⏭ Skipping {problem_id} (already exists)")
            return

        url = BASE_URL.format(problem_id)
        print(f"➡ {problem_id}")

        driver.get(url)
        print(f"URL= {url}")

        # 🔹 Wait for problem statement
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "problem-statement"))
        )

        # 🔹 Extract HTML BEFORE modifying DOM
        element = driver.find_element(By.ID, "problem-statement")
        html_content = element.get_attribute("outerHTML")

        # ✅ Save HTML
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

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

        # ✅ Save PDF
        with open(pdf_path, "wb") as f:
            f.write(base64.b64decode(pdf['data']))

        print(f"✅ Saved {problem_id}.html + .pdf")

    except Exception as e:
        print(f"❌ Failed {problem_id}: {e}")
        FAILED_TO_DOWNLOAD.add(problem_id)


def main():
    args = parse_args()
    DOWNLOAD_ONLY_NEW = args.only_new  # 🔥 flag
    DOWNLOAD_MCQ=args.mcq
    driver = setup_driver()
    problem_ids = read_problem_ids(DOWNLOAD_MCQ)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
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
            #save_problem(driver, pid)
            #save_problem(driver, pid, DOWNLOAD_ONLY_NEW)
            save_page_as_pdf(driver, pid, DOWNLOAD_ONLY_NEW) # "https://example.com", "example.pdf")

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
    print(f"Failed to Download:",FAILED_TO_DOWNLOAD)


if __name__ == "__main__":
    main()
