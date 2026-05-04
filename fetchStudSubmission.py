import csv
import time
import argparse
import json
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
def parse_all_assesments(html):
    soup = BeautifulSoup(html, "html.parser")

    table = soup.select_one("div.tablebox table.dataTable")
    if not table:
        return []

    tbody = table.find("tbody")
    if not tbody:
        return []

    rows = tbody.find_all("tr")

    results = []

    for row in rows:
        cells = row.find_all("td")

        if len(cells) < 10:
            continue

        data = {
            "id": cells[0].get_text(strip=True),
            "datetime": cells[1].get_text(strip=True),
            "username": cells[2].get_text(strip=True),
            "problem_code": cells[3].get_text(strip=True),
            "contest_code": cells[4].get_text(strip=True),

            "result": (
                cells[5].find("span").get("title", "").strip()
                if cells[5].find("span") else ""
            ),

            "time": cells[6].get_text(strip=True),
            "memory": cells[7].get_text(strip=True),
            "language": cells[8].get_text(strip=True),

            "solution_link": (
                cells[9].find("a")["href"]
                if cells[9].find("a") else ""
            )
        }

        results.append(data)

    return results

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
        writer.writerow(["Roll","Link1","Code1","Marks","Link2" ,"Code2","Marks","PlagScan","Code1LineCount","Code2LineCount"])

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
    rechecklist=[]

    for i, (roll, url1, url2) in enumerate(input_rows):
        print(f"➡ Processing Roll: {roll} {i}/{len(input_rows)}")

        html1 = fetch_html(driver, url1)
        table_data1 = parse_tablebox_table(html1)
        table_data1 = table_data1 or "NA"
        html2 = fetch_html(driver, url2)
        table_data2 = parse_tablebox_table(html2)
        table_data2 = table_data2 or "NA"
        # Check if the student appeared in a different contest or not
        if(table_data1=="NA" and table_data2=="NA"):
            new_url = modify_url(url1, condition=False)
            html1 = fetch_html(driver, new_url)
            all_assessments=parse_all_assesments(html1)
            output_rows.append([roll, all_assessments,json.dumps(all_assessments)])
            rechecklist.append([(roll, new_url)])
            if args.debug:
                print([roll, json.dumps(all_assessments)])
            if args.debug:
                print("🐞 Debug mode ON — wait to continue.")
                input("Press ENTER to continue...")
            continue

        # Fetch the student code
        code1 = None
        code2 = None
        if(table_data1!="NA"):
            studentsub1=fetch_html(driver,"https://www.codechef.com/viewsolution/"+table_data1)

            code1=extract_code_from_html(studentsub1)
        if(table_data2!="NA"):
            studentsub2=fetch_html(driver,"https://www.codechef.com/viewsolution/"+table_data2)
            code2=extract_code_from_html(studentsub2)
        code1 = code1 or "NA"
        code2 = code2 or "NA"
        print("https://www.codechef.com/viewsolution/"+table_data1, code1.count('\n'), "https://www.codechef.com/viewsolution/"+table_data2,code2.count('\n'))
        formula1 = '=BYROW(C2:C, LAMBDA(cell, IF(cell="", 0, COUNTA(SPLIT(cell, CHAR(10))))))' if i == 0 else ""
        formula2 = '=BYROW(F2:F, LAMBDA(cell, IF(cell="", 0, COUNTA(SPLIT(cell, CHAR(10))))))' if i == 0 else ""
        output_rows.append([roll, "https://www.codechef.com/viewsolution/"+table_data1, code1,"", "https://www.codechef.com/viewsolution/"+table_data2, code2,"","",formula1,formula2])
        if args.debug:
            print([roll, table_data1, code1, table_data2, code2])

        time.sleep(2)

    write_output_tsv(args.output, output_rows)
    print(f"\n Done. Output saved to {args.output}")
    #print(rechecklist)
    for x in rechecklist:
        print(x)

    if args.debug:
        print("🐞 Debug mode ON — browser will stay open.")
        input("Press ENTER to close browser...")
        driver.quit()
    else:
        driver.quit()
    print(f"\n🎯 End of simulation")


if __name__ == "__main__":
    main()