#!/bin/bash

# Check if a file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <file_with_executables>"
    exit 1
fi

# Read the file line by line
while IFS= read -r program; do
    if command -v "$program" &> /dev/null; then
        echo "Launching $program..."
        nohup "$program" >/dev/null 2>&1 &
    else
        echo "Error: $program not found."
    fi
done < "$1"

echo "All programs launched!"
