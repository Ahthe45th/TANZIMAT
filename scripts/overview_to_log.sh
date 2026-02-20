#!/bin/bash

# Ensure GUI prompts are shown on the correct display
export DISPLAY=:0

# The file containing the list of tasks
OVERVIEW_FILE="$HOME/Proyectos/TANZIMAT/NAFSIYYAH/Overview.md"

# Check if the overview file exists
if [ ! -f "$OVERVIEW_FILE" ]; then
    rofi -e "Error: Overview file not found at $OVERVIEW_FILE"
    exit 1
fi

# Use rofi to select one or more lines from the file and store them in a variable
selected_lines=$(cat "$OVERVIEW_FILE" | rofi -dmenu -p "Select Task(s)" -multi-select)

# Check if the user cancelled the selection
if [ -z "$selected_lines" ]; then
    exit 0
fi

# Loop over the selected lines using a heredoc to avoid stdin conflicts
while IFS= read -r selected_line; do
    # For each selected line, ask for more details using rofi

    # Skip empty lines that might result from selection
    if [ -z "$selected_line" ]; then
        continue
    fi

    start_time=$(rofi -dmenu -p "Start Time (24hr) for: ${selected_line:0:50}..." < /dev/null)
    end_time=$(rofi -dmenu -p "End Time (24hr) for: ${selected_line:0:50}..." < /dev/null)
    note=$(rofi -dmenu -p "Note for: ${selected_line:0:50}..." < /dev/null)

    # Create a temporary file to store the agenda item details
    temp_file=$(mktemp /tmp/agenda_item.XXXXXX)

    # Write the details to the temporary file
    echo "Task: $selected_line" > "$temp_file"
    echo "Start Time: $start_time" >> "$temp_file"
    echo "End Time: $end_time" >> "$temp_file"
    echo "Note: $note" >> "$temp_file"

    # Add a reminder
    /home/mehmet/miniconda3/envs/idris/bin/python /home/mehmet/Proyectos/TANZIMAT/scripts/add_reminder.py \
        --time "$start_time" \
        --file "$temp_file" \
        --label "agenda item"

    # Echo the collected information
    echo "---"
    echo "Task: $selected_line"
    echo "Start Time: $start_time"
    echo "End Time: $end_time"
    echo "Note: $note"
done <<< "$selected_lines"
