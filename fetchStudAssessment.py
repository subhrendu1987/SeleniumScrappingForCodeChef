import csv
import time
import argparse
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from auth import wait_for_manual_login

# Extract code from assessment page
def extract_code_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    editor = soup.find("div", id="submit-ide-v2")
    if not editor:
        return ""

    text_layer = editor.find("div", class_="ace_text-layer")
    if not text_layer:
        return ""

    lines = text_layer.find_all("div", class_="ace_line")

    code_lines = []
    for line in lines:
        # Preserve exact spacing between tokens
        text = line.get_text("", strip=False)

        # Remove trailing whitespace but keep indentation
        text = text.rstrip()

        code_lines.append(text)

    return "\n".join(code_lines)
# Fetch AssessmentID from URL
def parse_tablebox_table(html):
    soup = BeautifulSoup(html, "html.parser")

    # 🔹 Locate table
    table = soup.select_one("div.tablebox table.dataTable")
    if not table:
        return None

    # 🔹 Go inside tbody → first row
    tbody = table.find("tbody")
    if not tbody:
        return None

    first_row = tbody.find("tr")
    if not first_row:
        return None

    cells = first_row.find_all("td")

    if len(cells) < 10:
        return None

    # 🔹 Extract structured fields
    data = {
        "id": cells[0].get_text(strip=True),
        "datetime": cells[1].get_text(strip=True),
        "username": cells[2].get_text(strip=True),
        "problem_code": cells[3].get_text(strip=True),
        "contest_code": cells[4].get_text(strip=True),

        # ⭐ IMPORTANT: result is inside nested span → use title
        "result": (
            cells[5].find("span").get("title", "").strip()
            if cells[5].find("span") else ""
        ),

        "time": cells[6].get_text(strip=True),
        "memory": cells[7].get_text(strip=True),
        "language": cells[8].get_text(strip=True),

        # 🔹 Extract solution link
        "solution_link": (
            cells[9].find("a")["href"]
            if cells[9].find("a") else ""
        )
    }
    return data.get("id", "NA") or "NA"

# Fetch All Assessments
from bs4 import BeautifulSoup
import re

def getReportTable(html):
    soup = BeautifulSoup(html, "html.parser")
    result = {}

    for prob in soup.find_all("div", class_=re.compile(r"_prob_")):

        code = None
        qtype = None

        tags = prob.find_all("span", class_=re.compile(r"_tag_"))

        for tag in tags:
            key_tag = tag.find("span", class_=re.compile(r"_tagKey_"))
            if not key_tag:
                continue

            key_text = key_tag.get_text(strip=True)

            value = tag.get_text(strip=True).replace(key_text, "").strip()

            if "Code" in key_text:
                code = value
            elif "Type" in key_text:
                qtype = value

        if not code:
            continue

        # default fallback (just in case)
        if not qtype:
            qtype = "Unknown"

        # 🎯 extract score
        score_div = prob.find("div", class_=re.compile(r"_score_"))
        if not score_div:
            continue

        score = score_div.get_text(strip=True).replace(" ", "")

        # 🔥 new key format
        key = f"{qtype}: {code}"

        result[key] = score

    return result
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


import csv

def read_input_tsv(file_path, skip_lines=2):
    data = []

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")

        # 🔥 skip initial lines
        for _ in range(skip_lines):
            next(reader, None)

        # ✅ read header row
        headers = next(reader, None)
        if not headers:
            return data

        headers = [h.strip() for h in headers]

        for row in reader:
            if not any(row):  # skip empty rows
                continue

            # pad row if shorter than headers
            row = row + [""] * (len(headers) - len(row))

            row_dict = {
                headers[i]: row[i].strip() if i < len(row) else ""
                for i in range(len(headers))
            }
            print(row_dict)
            #data.append(row_dict)
            if row_dict["RollNo"]:
                data.append((row_dict["RollNo"], row_dict["ContestID"], row_dict["Report"]))

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
    if not rows:
        return

    # 🔥 collect all keys across rows
    headers = set()
    for row in rows:
        headers.update(row.keys())

    # keep important columns first
    priority = ["Roll", "ReportURL"]
    other_cols = sorted(h for h in headers if h not in priority)
    final_headers = priority + other_cols

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=final_headers, delimiter="\t")

        writer.writeheader()

        for row in rows:
            writer.writerow(row)

def modify_url(url, condition):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    # condition NOT satisfied → set pcode = All
    if not condition:
        query["pcode"] = ["All"]

    # rebuild query string
    new_query = urlencode(query, doseq=True)

    # rebuild full URL
    return urlunparse(parsed._replace(query=new_query))

def main():
    args = parse_args()

    driver = setup_driver()
    wait_for_manual_login(driver)

    input_rows = read_input_tsv(args.input)

    output_rows = []
    rechecklist = []

    for i, (roll, contestID, reportID) in enumerate(input_rows):
        print(f"➡ Processing Roll: {roll} {i+1}/{len(input_rows)}")

        reportURL = f"https://www.codechef.com/manage/{contestID}/report/{reportID}"

        html = fetch_html(driver, reportURL)
        parsed = getReportTable(html)

        row = {
            "Roll": roll,
            "ReportURL": reportURL,
            **parsed
        }

        output_rows.append(row)

        print(row)  # cleaner debug

        time.sleep(2)

    # ✅ write proper TSV
    write_output_tsv(args.output, output_rows)

    print(f"\n✅ Done. Output saved to {args.output}")

    if rechecklist:
        print("\n⚠ Recheck list:")
        for x in rechecklist:
            print(x)

    if args.debug:
        print("🐞 Debug mode ON — browser will stay open.")
        input("Press ENTER to close browser...")
    
    driver.quit()
    print("\n🎯 End of simulation")


if __name__ == "__main__":
    main()