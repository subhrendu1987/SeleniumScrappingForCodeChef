import csv
import time
import argparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# -----------------------------
# Files
# -----------------------------
INPUT_TSV = "CodechefTopicURL.tsv"
OUTPUT_TSV = "ProblemURL.tsv"


# -----------------------------
# Args
# -----------------------------
def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--max",
        type=int,
        default=-1,
        help="Limit number of subtopics to process (-1 = no limit)"
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

    service = Service("/usr/bin/chromedriver")  # adjust if needed

    driver = webdriver.Chrome(service=service, options=options)
    return driver


def wait_for_manual_login(driver):
    driver.get("https://www.codechef.com/")
    print("\n🔐 Please login manually in the opened browser...")
    input("👉 Press ENTER after login...")


# -----------------------------
# Read TSV
# -----------------------------
def read_topic_entries():
    entries = []

    with open(INPUT_TSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            topic = row["Topic"].strip()
            subtopic = row["Subtopic"].strip()
            url = row["URL"].strip()

            entries.append((topic, subtopic, url))

    return entries


# -----------------------------
# Core crawling logic
# -----------------------------
def extract_problem_urls(driver, topic, subtopic, start_url):
    collected_urls = []
    visited = set()

    print(f"   🌐 Opening: {start_url}")
    driver.get(start_url)

    while True:
        try:
            # Ensure page is loaded
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            current_url = driver.current_url

            if current_url not in visited:
                print(f"   ➕ {current_url}")
                collected_urls.append((topic, subtopic, current_url))
                visited.add(current_url)

            # Locate Next button (robust XPath)
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[.//span[contains(text(),'Next')]]")
                )
            )

            next_text = next_button.text.strip().lower()

            # Stop condition
            if "next module" in next_text:
                print("   ⛔ Reached Next Module")
                break

            next_href = next_button.get_attribute("href")

            if not next_href or next_href in visited:
                print("   ⚠ No new next link found")
                break

            # Navigate
            driver.get(next_href)
            time.sleep(1)

        except Exception as e:
            print(f"   ❌ Navigation error: {e}")
            break

    return collected_urls


# -----------------------------
# Save TSV
# -----------------------------
def save_problem_urls(all_urls):
    with open(OUTPUT_TSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")

        writer.writerow(["Topic", "Subtopic", "URL"])

        for row in all_urls:
            writer.writerow(row)

    print(f"\n📁 Saved URLs to {OUTPUT_TSV}")


# -----------------------------
# Main
# -----------------------------
def main():
    args = parse_args()
    max_limit = args.max

    driver = setup_driver()
    wait_for_manual_login(driver)

    entries = read_topic_entries()
    print(f"\n📄 Total subtopics found: {len(entries)}")

    all_problem_urls = []
    count = 0

    for topic, subtopic, url in entries:
        if max_limit != -1 and count >= max_limit:
            print("\n⏹ Max limit reached")
            break

        print(f"\n📘 Topic: {topic} | Subtopic: {subtopic}")

        try:
            urls = extract_problem_urls(driver, topic, subtopic, url)
            all_problem_urls.extend(urls)
            count += 1

        except Exception as e:
            print(f"⚠ Error processing {subtopic}: {e}")

            # Recover driver if needed
            try:
                driver.quit()
            except:
                pass

            driver = setup_driver()
            wait_for_manual_login(driver)

        time.sleep(2)

    driver.quit()

    save_problem_urls(all_problem_urls)

    print(f"\n🎯 Total subtopics processed: {count}")
    print(f"📦 Total URLs collected: {len(all_problem_urls)}")


# -----------------------------
# Entry
# -----------------------------
if __name__ == "__main__":
    main()
