#!/bin/bash
export DISPLAY=:0

# Define the directory for reminder content files
REMINDER_CONTENT_DIR="/home/mehmet/Proyectos/TANZIMAT/reminders_content"
mkdir -p "$REMINDER_CONTENT_DIR" # Ensure the directory exists

# Prompt for reminder time
TIME=$(rofi -dmenu -i -p "Enter reminder time (HH:MM)")
if [ -z "$TIME" ]; then
    exit 1
fi

# Prompt for the actual reminder content/message
REMINDER_MESSAGE=$(rofi -dmenu -i -p "Enter the reminder message")
if [ -z "$REMINDER_MESSAGE" ]; then
    exit 1
fi

# Prompt for a unique label for the reminder
LABEL=$(rofi -dmenu -i -p "Enter a unique label for the reminder")
if [ -z "$LABEL" ]; then
    exit 1
fi

# Create a unique filename for the reminder content
# Using label and current timestamp for uniqueness
FILENAME="${LABEL// /_}" # Replace spaces in label with underscores
FILENAME="${FILENAME//[^a-zA-Z0-9_.-]/}" # Sanitize filename
FILENAME="$(date +%Y%m%d%H%M%S)_${FILENAME}.txt"
FULL_FILE_PATH="$REMINDER_CONTENT_DIR/$FILENAME"

# Write the reminder message to the file
echo "$REMINDER_MESSAGE" > "$FULL_FILE_PATH"

# Call add_reminder.py with the new file path
/home/mehmet/miniconda3/envs/idris/bin/python /home/mehmet/Proyectos/TANZIMAT/scripts/add_reminder.py --time "$TIME" --file "$FULL_FILE_PATH" --label "$LABEL"

notify-send "Reminder Added" "Reminder with label '$LABEL' has been added. Content saved to: $FULL_FILE_PATH"

