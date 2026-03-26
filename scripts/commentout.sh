#!/bin/bash

set -e

file="$1"

if [[ -z "$file" ]]; then
    echo "Usage: $0 <file>"
    exit 1
fi

if [[ ! -f "$file" ]]; then
    echo "File not found: $file"
    exit 1
fi

# Get last line
last_line=$(tail -n 1 "$file")

# Check if already commented (allow leading spaces)
if [[ "$last_line" =~ ^[[:space:]]*# ]]; then
    exit 0
fi

# Comment last line in-place
sed -i '$ s/^[[:space:]]*/&#/' "$file"
