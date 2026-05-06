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
###################################################################################
### INPUT TSV FILES SET FIELD NAMES
FIELD_MAP = {
    "roll": ["rollno"],                 # ONLY rollno
    "user_id": ["userid"],              # NEW field
    "contest_id": ["contestid", "contest"],
    "report_id": ["assessmentreportlink", "report", "reportid"]
}
###################################################################################
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
###################################################################################
def time_to_seconds(t):
    mins, secs = map(int, t.split(":"))
    return mins * 60 + secs
###################################################################################
def has_code_similarity(html_data: str) -> bool:
    soup = BeautifulSoup(html_data, "html.parser")
    return bool(soup.find(string=lambda x: x and "Code Similarity Report" in x))
###################################################################################
def parse_code_similarity(html: str):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.find(string=lambda x: x and "Code Similarity Report" in x)
    if not title:
        return {}

    section = title.find_parent("div", class_="_card_h5z5l_1")
    if not section:
        return {}

    rows = section.select("div._row_17ctx_13")
    if not rows:
        return {}

    headers = [c.get_text(strip=True) for c in rows[0].select("div")]

    result = []
    for row in rows[1:]:
        cells = row.select("div._cell_17ctx_27")
        row_data = {}

        for i, cell in enumerate(cells):
            key = headers[i] if i < len(headers) else f"col_{i}"
            link = cell.find("a")
            row_data[key] = link["href"] if link else cell.get_text(strip=True)

        result.append(row_data)

    return {"code_similarity": result} if result else {}
###################################################################################
def parse_submission_history(html):
    soup = BeautifulSoup(html, "html.parser")
    result = []

    rows = soup.find_all("div", class_=lambda x: x and "_row_" in x)

    if not rows:
        return result

    # ---- headers ----
    header_cells = rows[0].find_all("div", class_=lambda x: x and "_cell_" in x)
    headers = [cell.get_text(strip=True).lower() for cell in header_cells]

    # ---- data rows ----
    for row in rows[1:]:
        cells = row.find_all("div", class_=lambda x: x and "_cell_" in x)

        if len(cells) != len(headers):
            continue

        row_data = {}

        for i in range(len(headers)):
            key = headers[i]

            # 🔥 Generic href extraction
            a_tag = cells[i].find("a", href=True)

            if a_tag:
                row_data[key] = a_tag["href"]
            else:
                row_data[key] = cells[i].get_text(" ", strip=True)

        result.append(row_data)

    return result
###################################################################################
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
###################################################################################
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
###################################################################################
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")  # adjust if needed

    return webdriver.Chrome(service=service, options=options)
###################################################################################
def normalize_header(h):
    return h.strip().lower().replace(" ", "")  # "Roll No" → "rollno"
###################################################################################
def resolve_schema(headers):
    resolved = {}

    for std_key, aliases in FIELD_MAP.items():
        for alias in aliases:
            alias = normalize_header(alias)
            if alias in headers:
                resolved[std_key] = alias
                break

    return resolved
###################################################################################
def read_input_tsv(file_path, skip_lines=0):
    data = []

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")

        for _ in range(skip_lines):
            next(reader, None)

        headers = next(reader, None)
        if not headers:
            return data

        headers = [normalize_header(h) for h in headers]

        # ✅ resolve once
        schema = resolve_schema(headers)

        for row in reader:
            if not any(row):
                continue

            row = row + [""] * (len(headers) - len(row))

            row_dict = {
                headers[i]: row[i].strip()
                for i in range(len(headers))
            }

            # ✅ attach resolved fields
            data.append({
                "roll": row_dict.get(schema.get("roll", ""), ""),
                "contest_id": row_dict.get(schema.get("contest_id", ""), ""),
                "report_id": row_dict.get(schema.get("report_id", ""), ""),
                "_raw": row_dict   # optional: keep full data
            })

    return data
###################################################################################
def write_output_tsv(output_file, rows):
    if not rows:
        return

    import csv

    headers = set()
    for row in rows:
        headers.update(row.keys())

    priority = ["Roll", "ReportURL"]

    def sort_key(h):
        if h in priority:
            return (-1, h)  # always first

        if h.startswith("MCQ"):
            return (0, h)

        if h.startswith("Programming"):
            return (1, h)

        if h.isdigit():
            return (2, int(h))

        return (3, h)  # fallback

    final_headers = sorted(headers, key=sort_key)

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=final_headers, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
###################################################################################
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
###################################################################################
def parse_report_url(report_url):
    if not report_url:
        return "", ""

    parts = urlparse(report_url).path.strip("/").split("/")

    # expected: manage/<contestID>/report/<userID>
    try:
        contest_idx = parts.index("manage") + 1
        report_idx = parts.index("report") + 1

        contestID = parts[contest_idx]
        userID = parts[report_idx]

        return contestID, userID
    except (ValueError, IndexError):
        return "", ""
###################################################################################
def main():
    args = parse_args()

    driver = setup_driver()
    wait_for_manual_login(driver)

    input_rows = read_input_tsv(args.input)

    output_rows = []
    rechecklist = []

    for i, row in enumerate(input_rows):
        roll = row["roll"]
        reportURL = row["report_id"]  # already full URL
        # ✅ extract IDs only if you need them
        contestID, userID = parse_report_url(reportURL)
        print(f"➡ Processing Roll: {roll} {i+1}/{len(input_rows)}")
        html = fetch_html(driver, reportURL)
        subHist = parse_submission_history(html)
        subHist.sort(key=lambda x: time_to_seconds(x.get("time", "0:00")), reverse=True)
        parsed = {str(i): row for i, row in enumerate(subHist)}
        ansTable=getReportTable(html)
        ansTable = dict(sorted(ansTable.items(), key=lambda x: (x[0].split(':')[0], x[0])))
        row = {
            "Roll": roll,
            "ReportURL": reportURL,
            **ansTable,
            **parsed
        }
        row = { **row,"plagScan": parse_code_similarity(html) if has_code_similarity(html) else ""}

        ### Fetch Codes
        latestSubmissionURLs = { prob: max((v for k, v in row.items() if k.isdigit() and v["problem"].startswith(prob)),key=lambda x: time_to_seconds(x["time"]),default=None)["view"]for prob in {v["problem"].split()[0] for k, v in row.items() if k.isdigit()}}
        html_of_codes_data = {prob: fetch_html(driver,url) for prob, url in latestSubmissionURLs.items() if url}

        codes={prob: extract_code_from_html(html_data) for prob,html_data in html_of_codes_data.items() if html_data}
        row.update({f"code_{k}": v for k, v in codes.items()})



        ### Finished Processing and save temporarily
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