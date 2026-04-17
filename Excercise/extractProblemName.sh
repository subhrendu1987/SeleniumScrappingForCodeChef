#!/bin/bash

DIR="$1"

if [ -z "$DIR" ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

for file in "$DIR"/*.html; do
    [ -e "$file" ] || continue   # handle no matches

    name=$(grep -oP '<h3 class="notranslate">\K[^<]+' "$file" | head -n 1)
    echo "$(basename "$file") -> $name"
done
