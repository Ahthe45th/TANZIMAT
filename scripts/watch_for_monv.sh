#!/bin/bash

MONITOR_DIR="/home/mehmet/Proyectos/"
SHOW_REMINDER_SCRIPT="/home/mehmet/Proyectos/TANZIMAT/scripts/show_reminder_by_label.py"
LABEL="Meta Ads Manager"

while true; do
  inotifywait -r -e create "$MONITOR_DIR" |
    while read -r directory event file; do
      if [[ "$file" == *.monv ]]; then
        echo "Detected .monv file creation: $file"
        python "$SHOW_REMINDER_SCRIPT" "$LABEL"
      fi
    done
done
