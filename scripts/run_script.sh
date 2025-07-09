#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Get a list of python scripts in the directory
SCRIPTS=$(ls $SCRIPT_DIR/*.py | xargs -n 1 basename)

# Show a rofi menu with the scripts
SELECTED_SCRIPT=$(echo "$SCRIPTS" | rofi -dmenu -p "Select a script to run")

# If a script was selected, run it
if [ -n "$SELECTED_SCRIPT" ]; then
    /home/mehmet/miniconda3/envs/idris/bin/python $SCRIPT_DIR/$SELECTED_SCRIPT
fi
