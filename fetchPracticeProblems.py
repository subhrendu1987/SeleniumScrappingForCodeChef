import csv
import os
import time
import base64
import re
import argparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


CSV_FILE = "PracticeProblems.tsv"
OUTPUT_DIR = "Excercise"

OUTPUT_HTML_DIR = os.path.join(OUTPUT_DIR, "html")
OUTPUT_PDF_DIR = os.path.join(OUTPUT_DIR, "pdf")

FAILED_TO_DOWNLOAD = []
MAX_DOWNLOADS = -1  # -1 = no limit

os.makedirs(OUTPUT_HTML_DIR, exist_ok=True)
os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)


# -----------------------------
# Utils
# -----------------------------
def sanitize_name(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def get_problem_id_from_url(url):
    return url.rstrip("/").split("/")[-1]


# -----------------------------
# Args
# -----------------------------
def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--only-new",
        action="store_true",
        help="Download only problems not already downloaded"
    )

    return parser.parse_args()


# -----------------------------
# Selenium setup
# -----------------------------
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")  # adjust path if needed

    driver = webdriver.Chrome(service=service, options=options)
    return driver


def wait_for_manual_login(driver):
    driver.get("https://www.codechef.com/")
    print("\n🔐 Login manually...")
    input("👉 Press ENTER after login...")


# -----------------------------
# TSV Parsing
# -----------------------------
def read_problem_entries():
    entries = []
    current_group = "Ungrouped"

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")

        for row in reader:
            for cell in row:
                if not cell or not cell.strip():
                    continue

                value = cell.strip()

                if value.startswith("http"):
                    entries.append((current_group, value))
                else:
                    current_group = value  # group title

    return entries


# -----------------------------
# Core logic
# -----------------------------
def save_problem(driver, url, group, only_new=False):
    try:
        problem_id = get_problem_id_from_url(url)
        group = sanitize_name(group)

        html_dir = os.path.join(OUTPUT_HTML_DIR, group)
        pdf_dir = os.path.join(OUTPUT_PDF_DIR, group)

        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(pdf_dir, exist_ok=True)

        html_path = os.path.join(html_dir, f"{problem_id}.html")
        pdf_path = os.path.join(pdf_dir, f"{problem_id}.pdf")

        # Skip existing
        if only_new and os.path.exists(html_path) and os.path.exists(pdf_path):
            print(f"⏭ Skipping {problem_id}")
            return

        print(f"➡ [{group}] {problem_id}")
        driver.get(url)

        # Wait for problem statement
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "problem-statement"))
        )

        element = driver.find_element(By.ID, "problem-statement")
        html_content = element.get_attribute("outerHTML")

        # Save HTML
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Clean page for PDF
        driver.execute_script("""
            document.body.innerHTML =
            document.getElementById('problem-statement').outerHTML;
        """)

        time.sleep(1)

        pdf = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True
        })

        with open(pdf_path, "wb") as f:
            f.write(base64.b64decode(pdf['data']))

        print(f"✅ Saved {problem_id}")

    except Exception as e:
        print(f"❌ Failed {url}: {e}")
        FAILED_TO_DOWNLOAD.append(url)


# -----------------------------
# Main
# -----------------------------
def main():
    args = parse_args()
    DOWNLOAD_ONLY_NEW = args.only_new

    driver = setup_driver()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    wait_for_manual_login(driver)

    entries = read_problem_entries()
    print(f"📄 Total entries found: {len(entries)}")

    count = 0

    for group, url in entries:
        if MAX_DOWNLOADS != -1 and count >= MAX_DOWNLOADS:
            print("Download limit reached")
            break

        try:
            save_problem(driver, url, group, DOWNLOAD_ONLY_NEW)
            count += 1

        except Exception as e:
            print(f"⚠ Unexpected error: {e}")

            try:
                driver.quit()
            except:
                pass

            driver = setup_driver()
            wait_for_manual_login(driver)

        time.sleep(2)

    driver.quit()

    print(f"\n🎯 Total downloaded: {count}")
    print(f"❌ Failed to Download: {FAILED_TO_DOWNLOAD}")


# -----------------------------
# Entry
# -----------------------------
if __name__ == "__main__":
    main()
