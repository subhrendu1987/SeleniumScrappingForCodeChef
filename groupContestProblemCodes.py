import csv
from collections import defaultdict

INPUT_FILE = "parsed_problems.csv"
OUTPUT_FILE = "grouped_problems.tsv"


def group_problem_codes():
    grouped = defaultdict(list)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            contest = row["ContestCode"].strip()
            problem = row["ProblemCode"].strip()

            if problem:
                grouped[contest].append(problem)

    return grouped


def save_grouped_data(grouped):
    # 🔹 Find maximum number of problems in any contest
    max_problems = max(len(v) for v in grouped.values())

    # 🔹 Create dynamic headers
    headers = ["ContestCode"] + [f"P{i+1}" for i in range(max_problems)]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f,delimiter="\t")
        writer.writerow(headers)

        for contest, problems in grouped.items():
            # 🔹 Remove duplicates (preserve order)
            unique_problems = list(dict.fromkeys(problems))

            # 🔹 Pad with empty strings if needed
            row = [contest] + unique_problems
            row += [""] * (max_problems - len(unique_problems))

            writer.writerow(row)

    print(f"✅ Saved: {OUTPUT_FILE}")


def main():
    grouped = group_problem_codes()
    print(grouped)
    save_grouped_data(grouped)


if __name__ == "__main__":
    main()
