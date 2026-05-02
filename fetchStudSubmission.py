import csv
import time
import argparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from auth import wait_for_manual_login

def parse_tablebox_table(html):
    """
    Extracts table inside <div class="tablebox"> with <table class="dataTable">
    Returns: list of rows (each row = list of cell text)
    """

    soup = BeautifulSoup(html, "html.parser")

    # 🔹 Find the div
    div = soup.find("div", class_="tablebox")
    if not div:
        return []

    # 🔹 Find the table
    table = div.find("table", class_="dataTable")
    if not table:
        return []

    parsed_data = []

    # 🔹 Extract rows
    for tr in table.find_all("tr"):
        row = []

        # handle both th and td
        cells = tr.find_all(["th", "td"])

        for cell in cells:
            text = cell.get_text(strip=True)
            row.append(text)

        if row:
            parsed_data.append(row)

    return parsed_data


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True, help="Input TSV file")
    parser.add_argument("--output", required=True, help="Output TSV file")

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Keep browser open after execution"
    )

    return parser.parse_args()

def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")  # adjust if needed

    return webdriver.Chrome(service=service, options=options)


def read_input_tsv(file_path):
    data = []

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")

        # 🔥 skip first 3 rows
        for _ in range(3):
            next(reader, None)

        for row in reader:
            if len(row) < 3:
                continue

            roll = row[0].strip()
            url1 = row[1].strip()
            url2 = row[2].strip()

            if roll:
                data.append((roll, url1, url2))

    return data


def fetch_html(driver, url):
    if not url:
        return ""

    try:
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(1)  # allow dynamic content

        return driver.page_source

    except Exception as e:
        print(f"❌ Failed URL: {url} | {e}")
        return ""


def write_output_tsv(output_file, rows):
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")

        # header
        writer.writerow(["Roll", "HTML1", "HTML2"])

        for row in rows:
            writer.writerow(row)


def main():
    args = parse_args()

    driver = setup_driver()
    wait_for_manual_login(driver)

    input_rows = read_input_tsv(args.input)

    output_rows = []

    for roll, url1, url2 in input_rows:
        print(f"➡ Processing Roll: {roll}")

        html1 = fetch_html(driver, url1)
        table_data1 = parse_tablebox_table(html1)
        html2 = fetch_html(driver, url2)
        table_data2 = parse_tablebox_table(html2)

        output_rows.append([roll, table_data1, table_data2])

        time.sleep(2)

    write_output_tsv(args.output, output_rows)
    print(f"\n Done. Output saved to {args.output}")

    if args.debug:
        print("🐞 Debug mode ON — browser will stay open.")
        input("Press ENTER to close browser...")
        driver.quit()
    else:
        driver.quit()
    print(f"\n🎯 End of simulation")


if __name__ == "__main__":
    main()