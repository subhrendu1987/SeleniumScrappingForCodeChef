#!/bin/bash

show_help() {
    echo "Usage:"
    echo "  $0 <directory>"
    echo "  $0 <tsv_file>"
    echo ""
    echo "Description:"
    echo "  Mode 1 (Directory input):"
    echo "    Extracts problem titles from all HTML files in the directory."
    echo ""
    echo "  Mode 2 (TSV input):"
    echo "    Reads TSV with columns: Topic  Subtopic  URL"
    echo "    Finds corresponding HTML files in:"
    echo "      Excercise/html/<Topic>/<Subtopic>/"
    echo "    Outputs TSV with:"
    echo "      Topic  Subtopic  URL  Problem Title"
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 ./html"
    echo "  $0 ../CSVs/ProblemURL.tsv"
}

INPUT="$1"

if [[ "$INPUT" == "-h" || "$INPUT" == "--help" ]]; then
    show_help
    exit 0
fi

if [ -z "$INPUT" ]; then
    show_help
    exit 1
fi

# ------------------------------
# Mode 1: Directory input (existing functionality)
# ------------------------------
if [ -d "$INPUT" ]; then
    for file in "$INPUT"/*.html; do
        [ -e "$file" ] || continue

        name=$(grep -oP '<h3 class="notranslate">\K[^<]+' "$file" | head -n 1)
        echo -e "$(basename "$file")\t$name"
    done
    exit 0
fi





# ------------------------------
# Mode 2: TSV input (new functionality)
# ------------------------------
# ---- trim function (inline, no external tools) ----
trim() {
    local var="$1"
    var="${var#"${var%%[![:space:]]*}"}"
    var="${var%"${var##*[![:space:]]}"}"
    echo -n "$var"
}

build_filepath() {
    local BASE_DIR="$1"
    local topic="$2"
    local subtopic="$3"
    local filename="$4"



    # ---- clean inputs ----
    topic=$(trim "$topic")
    subtopic=$(trim "$subtopic")
    filename=$(trim "$filename")

    # ---- remove URL params/fragments if filename came from URL ----
    filename="${filename%%[\?#]*}"

    # ---- extract basename (in case full URL passed) ----
    filename=$(basename "$filename")

    # ---- ensure .html extension ----
    [[ "$filename" != *.html ]] && filename="${filename}.html"

    # ---- construct path ----
    local filepath="$BASE_DIR/$topic/$subtopic/$filename"

    echo "$filepath"
}




if [ -f "$INPUT" ]; then

    BASE_DIR="./html"

    echo -e "Topic\tSubtopic\tURL\tProblem Title"
    

    tail -n +2 "$INPUT" | while IFS=$'\t' read -r topic subtopic url; do
        filepath=$(build_filepath "$BASE_DIR" "$topic" "$subtopic" "$url")
        if [ -f "$filepath" ]; then
            title=$(grep -oP '<h3 class="notranslate">\K[^<]+' "$filepath" | head -n 1)
            title=($trim $title)
            echo -e "$topic\t$subtopic\t$url\t$title"
        else
            #title="FILE_NOT_FOUND"
            echo "<NotFound>"
            echo -e "$filepath"
        fi

        
    done

    exit 0
fi

echo "Error: Input is neither a valid directory nor a TSV file."
exit 1
