#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Ensure logs directory exists
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Define the mapping of human-readable names to script filenames
declare -A SCRIPT_MAP
SCRIPT_MAP["Ad Balances"]="adbalances.py"
SCRIPT_MAP["Business Manager Write"]="income_recorder.py"
SCRIPT_MAP["Crop Screenshot"]="crop_screenshot.py"
SCRIPT_MAP["Flow Creator"]="flow_creator.py"
SCRIPT_MAP["Men Upload"]="menupload.py"
SCRIPT_MAP["Run Flow"]="run_flow.py"
SCRIPT_MAP["Send Ad Balances"]="sendadbalances.py"
SCRIPT_MAP["Send Bills Automatically"]="sendsbillsauto.py"
SCRIPT_MAP["Daily Shadow Work"]="dailyshadowwork.py"
SCRIPT_MAP["Show Purgatory"]="show_purgatory.py"
SCRIPT_MAP["Spend Aggregation"]="spend_recorder.py"
SCRIPT_MAP["Test Reminders"]="test_reminders.py"
SCRIPT_MAP["Git Sync"]="git_sync.sh"
SCRIPT_MAP["Kill Firefox"]="kill_firefox.sh"
SCRIPT_MAP["Reset Timer"]="resettimer.sh"
SCRIPT_MAP["Start Stop Timer"]="startstoptimer.sh"
SCRIPT_MAP["Timer"]="timer.sh"
SCRIPT_MAP["Timer Mode"]="timermode.sh"
SCRIPT_MAP["Strikethrough Line"]="strikethrough.sh"
SCRIPT_MAP["Ad Copy Integrator"]="adcopyintegrator.py"
SCRIPT_MAP["Run Codex"]="run_codex.sh"
SCRIPT_MAP["Add Prayer Reminders"]="add_prayer_reminders.py"
SCRIPT_MAP["Remove Prayer Reminders"]="remove_prayer_reminders.py"
SCRIPT_MAP["Log Overview Task"]="overview_to_log.sh"
SCRIPT_MAP["Log Maintenance Task"]="overview_to_log_maintenance.sh"
SCRIPT_MAP["Add to Project"]="add_to_project.sh"
SCRIPT_MAP["Add Reminder"]="rofi_add_reminder.sh"

# Define icons for each script
declare -A ICON_MAP
ICON_MAP["Ad Balances"]="cash"
ICON_MAP["Business Manager Write"]="briefcase"
ICON_MAP["Crop Screenshot"]="image-crop"
ICON_MAP["Flow Creator"]="object-select"
ICON_MAP["Men Upload"]="arrow-up"
ICON_MAP["Run Flow"]="media-playback-start"
ICON_MAP["Send Ad Balances"]="mail-send"
ICON_MAP["Send Bills Automatically"]="emblem-documents"
ICON_MAP["Daily Shadow Work"]="book"
ICON_MAP["Show Purgatory"]="dialog-warning"
ICON_MAP["Spend Aggregation"]="view-financial-charts"
ICON_MAP["Test Reminders"]="utilities-test"
ICON_MAP["Git Sync"]="vcs-sync"
ICON_MAP["Kill Firefox"]="firefox"
ICON_MAP["Reset Timer"]="edit-undo"
ICON_MAP["Start Stop Timer"]="media-record"
ICON_MAP["Timer"]="appointment-new"
ICON_MAP["Timer Mode"]="preferences-system"
ICON_MAP["Strikethrough Line"]="format-text-strikethrough"
ICON_MAP["Ad Copy Integrator"]="edit-paste"
ICON_MAP["Run Codex"]="brain"
ICON_MAP["Add Prayer Reminders"]="appointment-new"
ICON_MAP["Remove Prayer Reminders"]="edit-delete"
ICON_MAP["Log Overview Task"]="emblem-documents"
ICON_MAP["Log Maintenance Task"]="emblem-documents"
ICON_MAP["Add to Project"]="list-add"
ICON_MAP["Add Reminder"]="list-add"

# Generate options for rofi with icons
OPTIONS=""
# Use a while read loop to correctly handle names with spaces
while IFS= read -r name; do
    if [[ -z "$name" ]]; then continue; fi
    icon=${ICON_MAP[$name]:-application-x-executable} # Default icon
    OPTIONS+="$name\0icon\x1f$icon\n"
done < <(printf "%s\n" "${!SCRIPT_MAP[@]}" | sort)


# Show a rofi menu with the human-readable names and icons
# The '-i' flag makes the search case-insensitive
SELECTED_OPTION=$(echo -e "$OPTIONS" | rofi -dmenu -i -p "Select a script to run" -theme Adapta-Nokto -show-icons -width -30)

# If an option was selected, get the corresponding script filename and run it
if [ -n "$SELECTED_OPTION" ]; then
    SELECTED_SCRIPT=${SCRIPT_MAP[$SELECTED_OPTION]}

    if [[ "$SELECTED_SCRIPT" == *.py ]]; then
        /home/mehmet/miniconda3/envs/idris/bin/python "$SCRIPT_DIR/$SELECTED_SCRIPT"
    elif [[ "$SELECTED_SCRIPT" == *.sh ]]; then
        bash "$SCRIPT_DIR/$SELECTED_SCRIPT"
    fi
fi
