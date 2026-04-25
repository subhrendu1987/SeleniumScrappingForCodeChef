import os
import csv
from bs4 import BeautifulSoup


INPUT_DIR = "data"
OUTPUT_FILE = "parsed_problems.csv"


def extract_table_data(html_content, contest_code):
    soup = BeautifulSoup(html_content, "html.parser")

    table = soup.find("table")
    if not table:
        return []

    rows = table.find("tbody").find_all("tr")

    extracted = []

    for row in rows:
        cols = row.find_all("td")

        try:
            # 🔹 Problem Code
            problem_code = cols[0].get_text(strip=True)

            # 🔹 Start / End time (from input value)
            start_time = cols[2].find("input")["value"]
            end_time = cols[3].find("input")["value"]

            # 🔹 Info & Sub Limit
            info = cols[4].find("input")["value"]
            sub_limit = cols[5].find("input")["value"]

            # 🔹 Problem Type (selected option)
            select = cols[6].find("select")
            problem_type = select.find("option", selected=True)
            if problem_type:
                problem_type = problem_type.get_text(strip=True)
            else:
                problem_type = ""

            extracted.append([
                contest_code,
                problem_code,
                start_time,
                end_time,
                info,
                sub_limit,
                problem_type
            ])

        except Exception as e:
            print(f"⚠ Skipping row: {e}")

    return extracted


def process_all_files():
    all_data = []

    for file in os.listdir(INPUT_DIR):
        if file.endswith(".html"):
            contest_code = file.replace(".html", "")
            file_path = os.path.join(INPUT_DIR, file)

            print(f"➡ Processing {file}")

            with open(file_path, "r", encoding="utf-8") as f:
                html = f.read()

            data = extract_table_data(html, contest_code)
            all_data.extend(data)

    return all_data


def save_to_csv(data):
    headers = [
        "ContestCode",
        "ProblemCode",
        "StartTime",
        "EndTime",
        "Info",
        "SubLimit",
        "ProblemType"
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data)

    print(f"\n✅ Saved CSV: {OUTPUT_FILE}")


def main():
    data = process_all_files()
    save_to_csv(data)


if __name__ == "__main__":
    main()