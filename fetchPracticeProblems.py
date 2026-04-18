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


CSV_FILE = "CSVs/ProblemURL.tsv"
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
    driver.get("https://www.codechef.com/login?destination=/")
    print("\n🔐 Login manually...")
    input("👉 Press ENTER after login...")


# -----------------------------
# TSV Parsing (UPDATED)
# -----------------------------
def read_problem_entries():
    entries = []

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            topic = row["Topic"].strip()
            subtopic = row["Subtopic"].strip()
            url = row["URL"].strip()

            entries.append((topic, subtopic, url))

    return entries


# -----------------------------
# Core logic (UPDATED)
# -----------------------------
def save_problem(driver, url, topic, subtopic, only_new=False):
    try:
        problem_id = get_problem_id_from_url(url)

        topic = sanitize_name(topic)
        subtopic = sanitize_name(subtopic)

        # Hierarchical directories
        html_dir = os.path.join(OUTPUT_HTML_DIR, topic, subtopic)
        pdf_dir = os.path.join(OUTPUT_PDF_DIR, topic, subtopic)

        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(pdf_dir, exist_ok=True)

        html_path = os.path.join(html_dir, f"{problem_id}.html")
        pdf_path = os.path.join(pdf_dir, f"{problem_id}.pdf")

	# Always skip if both files already exist
	if os.path.exists(html_path) and os.path.exists(pdf_path):
	    print(f"⏭ Already exists: {problem_id}")
	    return

	# Optional: allow partial re-download logic
	if only_new and (os.path.exists(html_path) or os.path.exists(pdf_path)):
	    print(f"⏭ Skipping partial existing: {problem_id}")
	    return
        print(f"➡ [{topic} → {subtopic}] {problem_id}")
        driver.get(url)

        # Wait for problem statement
        WebDriverWait(driver, 20).until(
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
# Main (UPDATED)
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

    for topic, subtopic, url in entries:
        if MAX_DOWNLOADS != -1 and count >= MAX_DOWNLOADS:
            print("Download limit reached")
            break

        try:
            save_problem(driver, url, topic, subtopic, DOWNLOAD_ONLY_NEW)
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
