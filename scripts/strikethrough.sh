#!/bin/bash

export DISPLAY=:0

# If no argument is provided, use the default file path
if [ -z "$1" ]; then
  FILE_PATH="/home/mehmet/Proyectos/TANZIMAT/NAFSIYYAH/Overview.md"
else
  FILE_PATH="$1"
fi

# Use rofi to select a line from the file
SELECTED_LINE=$(rofi -dmenu -i -p "Select a line to toggle strikethrough" -width -90 < "$FILE_PATH")

# If a line was selected, toggle the strikethrough
if [ -n "$SELECTED_LINE" ]; then
  # Get the line number of the selected line.
  # -F for fixed string search, -x to match the whole line.
  # The -e flag ensures lines starting with '-' are treated as patterns, not options.
  # We use head -n 1 in case of duplicate lines.
  LINE_NUMBER=$(grep -n -F -x -e "$SELECTED_LINE" "$FILE_PATH" | head -n 1 | cut -d: -f1)

  if [ -n "$LINE_NUMBER" ]; then
    # Check if the line already has strikethrough
    if [[ "$SELECTED_LINE" == ~~*~~ ]]; then
      # Line has strikethrough, so remove it
      REPLACEMENT_STRING=${SELECTED_LINE:2:-2}
      notify_msg="Strikethrough removed: $REPLACEMENT_STRING"
    else
      # Line does not have strikethrough, so add it
      REPLACEMENT_STRING="~~$SELECTED_LINE~~"
      notify_msg="Strikethrough applied: $REPLACEMENT_STRING"
    fi

    # Escape for sed's replacement part. We need to escape '\', '&', and the delimiter '#'.
    ESCAPED_REPLACEMENT_STRING=$(echo "$REPLACEMENT_STRING" | sed -e 's/\\/\\\\/g' -e 's/&/\\&/g' -e 's/#/\\#/g')

    # Use sed to replace the specific line. The `.*` will match the whole line.
    sed -i "${LINE_NUMBER}s#.*#$ESCAPED_REPLACEMENT_STRING#" "$FILE_PATH"
    notify-send "$notify_msg"
  else
    # This case can happen if the file was modified between rofi selection and grep
    notify-send "Error: Could not find the selected line in the file."
  fi
fi

### Sync
/home/mehmet/miniconda3/envs/idris/bin/python /home/mehmet/Proyectos/TANZIMAT/scripts/synchronize_projects.py
