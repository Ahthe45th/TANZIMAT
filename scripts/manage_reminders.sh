#!/bin/bash

REMINDERS_FILE="$HOME/Proyectos/TANZIMAT/reminders.json"
ADD_REMINDER_SCRIPT="$HOME/Proyectos/TANZIMAT/scripts/add_reminder.py"

# Ensure GUI prompts are shown on the correct display
export DISPLAY=:0

# Check if reminders file exists (for deletion part)
if [ ! -f "$REMINDERS_FILE" ]; then
    # If file doesn't exist, only "Add Reminder" is a valid option
    ACTION=$(echo -e "Add Reminder" | rofi -dmenu -p "Manage Reminders")
else
    ACTION=$(echo -e "Add Reminder\nDelete Reminder" | rofi -dmenu -p "Manage Reminders")
fi

if [ -z "$ACTION" ]; then
    exit 0
fi

case "$ACTION" in
    "Add Reminder")
        TIME=$(rofi -dmenu -p "Enter Time (HH:MM) for new reminder")
        if [ -z "$TIME" ]; then exit 0; fi

        LABEL=$(rofi -dmenu -p "Enter Label for new reminder")
        if [ -z "$LABEL" ]; then exit 0; fi

        FILE=$(rofi -dmenu -p "Enter Absolute Path to Reminder File")
        if [ -z "$FILE" ]; then exit 0; fi

        # Call the add_reminder.py script
        python "$ADD_REMINDER_SCRIPT" --time "$TIME" --label "$LABEL" --file "$FILE"
        rofi -e "Reminder '$LABEL' added successfully."
        ;;
    "Delete Reminder")
        # Check if reminders file exists before trying to delete
        if [ ! -f "$REMINDERS_FILE" ]; then
            rofi -e "Error: Reminders file not found at $REMINDERS_FILE. Cannot delete."
            exit 1
        fi

        options=$(jq -r '.[] | .label + " (" + .time + ")"' "$REMINDERS_FILE")

        selected_reminders=$(echo -e "$options" | rofi -dmenu -p "Select reminder(s) to delete" -multi-select)

        if [ -z "$selected_reminders" ]; then
            exit 0
        fi

        temp_file=$(mktemp)
        cp "$REMINDERS_FILE" "$temp_file"

        while IFS= read -r selected; do
            label=$(echo "$selected" | sed -E 's/ \(.*\)//')
            time=$(echo "$selected" | sed -E 's/.*\((.*)\)/\1/')
            jq --arg label "$label" --arg time "$time" 'del(.[] | select(.label == $label and .time == $time))' "$temp_file" > "$temp_file.tmp" && mv "$temp_file.tmp" "$temp_file"
        done <<< "$selected_reminders"

        mv "$temp_file" "$REMINDERS_FILE"
        rofi -e "Deleted selected reminders."
        ;;
    *)
        exit 0
        ;;
esac
