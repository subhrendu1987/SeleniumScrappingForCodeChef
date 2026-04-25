#!/usr/bin/env python3

import os
from bs4 import BeautifulSoup

INPUT_DIR = "html"
OUTPUT_DIR = "txt"


def fix_katex_math(soup):
    """
    Keep proper math text from KaTeX by extracting only:
    <annotation encoding="application/x-tex">
    
    Example:
    <annotation>target</annotation>
    instead of broken:
    t a r g e t
    """
    for katex in soup.select(".katex"):
        annotation = katex.find("annotation")

        if annotation and annotation.text.strip():
            clean_math = annotation.text.strip()
            katex.replace_with(clean_math)
        else:
            katex.decompose()

    return soup


def html_to_text(html_content):
    """
    Convert HTML to clean readable text while preserving
    proper math values from KaTeX.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove unwanted tags
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Replace KaTeX blocks with proper math text
    soup = fix_katex_math(soup)

    # Extract text
    text = soup.get_text(separator="\n")

    # Clean excessive blank lines
    cleaned_lines = []
    prev_blank = False

    for line in text.splitlines():
        line = line.strip()

        if not line:
            if not prev_blank:
                cleaned_lines.append("")
            prev_blank = True
            continue

        prev_blank = False
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def process_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    clean_text = html_to_text(html_content)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(clean_text)

    print(f"Converted: {input_file} -> {output_file}")


def main():
    if not os.path.exists(INPUT_DIR):
        print(f"Input directory '{INPUT_DIR}' does not exist.")
        return

    for root, _, files in os.walk(INPUT_DIR):
        for file in files:
            if file.endswith((".html", ".htm")):
                input_file = os.path.join(root, file)

                # Preserve directory structure
                relative_path = os.path.relpath(root, INPUT_DIR)
                output_subdir = os.path.join(OUTPUT_DIR, relative_path)

                base_name = os.path.splitext(file)[0]
                output_file = os.path.join(output_subdir, base_name + ".txt")

                process_file(input_file, output_file)


if __name__ == "__main__":
    main()