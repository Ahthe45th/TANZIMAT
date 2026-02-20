#!/bin/bash

# Ensure GUI prompts are shown on the correct display
export DISPLAY=:0
PROJECTS_DIR="$HOME/Proyectos/TANZIMAT/NAFSIYYAH/Projects"

# Step 1: Choose Type
TYPE=$(echo -e "Current Action\nNote" | rofi -dmenu -p "Select Type" -lines 2)
if [ -z "$TYPE" ]; then
    exit 0
fi

# Step 2: Choose Project
# Get project list from filenames, removing the .md extension
PROJECT_LIST=$(ls -1 "$PROJECTS_DIR" | grep '\.md$' | sed 's/\.md$//')
PROJECT_NAME=$(echo "$PROJECT_LIST" | rofi -dmenu -p "Select or Create Project")
if [ -z "$PROJECT_NAME" ]; then
    exit 0
fi

# Step 3: Get multi-line content using Zenity
CONTENT=$(zenity --text-info --editable --title="Enter content for: $PROJECT_NAME" --width=500 --height=300)
# Check if user cancelled zenity dialog
if [ $? -ne 0 ]; then
    exit 0
fi
if [ -z "$CONTENT" ]; then
    echo "No content provided. Exiting."
    exit 0
fi

# Define target file and headings
PROJECT_FILE="$PROJECTS_DIR/$PROJECT_NAME.md"
CURRENT_ACTIONS_HEADING="### Current Actions"
NOTES_HEADING="### Notes"

# Step 4: Update File
# Create new project file if it doesn't exist
if [ ! -f "$PROJECT_FILE" ]; then
    echo "Creating new project: $PROJECT_NAME"
    # Create a template
    echo -e "$CURRENT_ACTIONS_HEADING\n\n$NOTES_HEADING\n" > "$PROJECT_FILE"
fi

# Determine content format and target heading based on type
if [ "$TYPE" == "Current Action" ]; then
    TARGET_HEADING="$CURRENT_ACTIONS_HEADING"
    # Format each line of the content as a task
    FORMATTED_CONTENT=$(echo "$CONTENT" | sed 's/^/- [ ] /')
else # Note
    TARGET_HEADING="$NOTES_HEADING"
    # Format each line of the content as a list item
    FORMATTED_CONTENT=$(echo "$CONTENT" | sed 's/^/- /')
fi

# Create a temporary file for the content to be inserted
TMP_CONTENT_FILE=$(mktemp)
echo -e "\n${FORMATTED_CONTENT}" > "$TMP_CONTENT_FILE"

# Check if target heading exists and add content
if grep -qFx "$TARGET_HEADING" "$PROJECT_FILE"; then
    # Heading exists, use sed 'r' command to read content from file and insert after pattern
    sed -i "/^${TARGET_HEADING}$/r $TMP_CONTENT_FILE" "$PROJECT_FILE"
else
    # Heading doesn't exist, so append the heading and content to the end of the file.
    echo -e "\n${TARGET_HEADING}" >> "$PROJECT_FILE"
    cat "$TMP_CONTENT_FILE" >> "$PROJECT_FILE"
fi
rm "$TMP_CONTENT_FILE"

# Clean up empty lines that might be added under headings
sed -i '/^###/{n;/^$/d;}' "$PROJECT_FILE"


notify-send "Successfully added $TYPE to $PROJECT_NAME."

/home/mehmet/miniconda3/envs/idris/bin/python ~/Proyectos/TANZIMAT/scripts/get_open_actions.py > ~/Proyectos/TANZIMAT/NAFSIYYAH/Overview.md
