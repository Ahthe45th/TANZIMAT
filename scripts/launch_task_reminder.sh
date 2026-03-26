#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOCK_FILE="/tmp/.tanzimat_mpv_zen_lock"

# Create the lock file immediately
touch "$LOCK_FILE"
echo "Lock file created: $LOCK_FILE"

# Ensure the lock file is removed if the script exits for any reason
trap "rm -f \"$LOCK_FILE\"; echo 'Lock file removed on exit: $LOCK_FILE'" EXIT INT TERM

echo "Launching Task Reminder System. mpv and zen processes will be killed while the reminder is active."

# Launch the process killer in the background
python3 "$SCRIPT_DIR/gui_scripts/process_killer.py" &
PROCESS_KILLER_PID=$!
echo "Process Killer started in background (PID: $PROCESS_KILLER_PID)."

# Launch the Python GUI script
python3 "$SCRIPT_DIR/gui_scripts/task_reminder_gui.py"

# Wait for the process killer to finish (it will exit when the lock file is removed by the GUI)
wait $PROCESS_KILLER_PID

echo "Task Reminder System closed. mpv and zen processes are no longer being killed."
