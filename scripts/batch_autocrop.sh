#!/usr/bin/env bash

# Directory with input files
INPUT_DIR="$HOME/Downloads/allscreenshots/screenshots/"

# Script to run
SCRIPT="$HOME/Proyectos/TANZIMAT/scripts/autocrop_instagram.py"

# Loop through all jpeg/jpg files
for file in "$INPUT_DIR"/*.jpeg "$INPUT_DIR"/*.png; do
  # Check file exists (avoids errors if no matches)
  [ -e "$file" ] || continue
  
  echo "Processing: $file"
  python "$SCRIPT" "$file"
done
