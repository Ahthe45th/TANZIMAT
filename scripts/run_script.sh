#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Ensure logs directory exists
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Define the mapping of human-readable names to script filenames
declare -A SCRIPT_MAP
SCRIPT_MAP["Ad Balances"]="adbalances.py"
SCRIPT_MAP["Business Manager Write"]="businessmanagerwrite.py"
SCRIPT_MAP["Crop Screenshot"]="crop_screenshot.py"
SCRIPT_MAP["Flow Creator"]="flow_creator.py"
SCRIPT_MAP["Menu Upload"]="menupload.py"
SCRIPT_MAP["Run Flow"]="run_flow.py"
SCRIPT_MAP["Send Ad Balances"]="sendadbalances.py"
SCRIPT_MAP["Send Bills Automatically"]="sendsbillsauto.py"
SCRIPT_MAP["Show Purgatory"]="show_purgatory.py"
SCRIPT_MAP["Spend Aggregation"]="spendaggregation.py"
SCRIPT_MAP["Git Sync"]="git_sync.sh"
SCRIPT_MAP["Kill Firefox"]="kill_firefox.sh"
SCRIPT_MAP["Reset Timer"]="resettimer.sh"
SCRIPT_MAP["Start Stop Timer"]="startstoptimer.sh"
SCRIPT_MAP["Timer"]="timer.sh"
SCRIPT_MAP["Timer Mode"]="timermode.sh"

# Get the human-readable names for the rofi menu
OPTIONS="$(printf "%s\n" "${!SCRIPT_MAP[@]}")"

# Show a rofi menu with the human-readable names
SELECTED_OPTION=$(echo "$OPTIONS" | rofi -dmenu -p "Select a script to run")

# If an option was selected, get the corresponding script filename and run it
if [ -n "$SELECTED_OPTION" ]; then
    SELECTED_SCRIPT=${SCRIPT_MAP[$SELECTED_OPTION]}
    if [[ "$SELECTED_SCRIPT" == *.py ]]; then
        /home/mehmet/miniconda3/envs/idris/bin/python "$SCRIPT_DIR/$SELECTED_SCRIPT"
    elif [[ "$SELECTED_SCRIPT" == *.sh ]]; then
        bash "$SCRIPT_DIR/$SELECTED_SCRIPT"
    fi
fi
