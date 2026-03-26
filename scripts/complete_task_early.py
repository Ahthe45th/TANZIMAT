#!/home/mehmet/miniconda3/envs/idris/bin/python3
import os
import sys
import subprocess
import time
from datetime import datetime

# Get the absolute path of the directory containing THIS script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from gui_utils import notify

LOG_FILE = os.path.join(SCRIPT_DIR, "logs/task_tracking.log")
CURRENT_TASK_FILE = "/tmp/current_task.txt"
TRACKER_SCRIPT = os.path.join(SCRIPT_DIR, "task_tracker.py")
PYTHON_EXEC = "/home/mehmet/miniconda3/envs/idris/bin/python3"

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def main():
    task = "Unknown"
    if os.path.exists(CURRENT_TASK_FILE):
        with open(CURRENT_TASK_FILE, "r") as f:
            task = f.read().strip()
        os.remove(CURRENT_TASK_FILE)

    log_event(f"EARLY COMPLETE - Task: {task}")
    notify("Task Tracker", f"Task '{task}' finished early. Restarting tracker.")

    # Use pkill -f to find the script by its full name
    subprocess.run(["pkill", "-f", TRACKER_SCRIPT])

    # Give it a second to terminate
    time.sleep(1)

    # Restart the script
    # We use nohup or just & in shell to detach it, but here we can just spawn it
    subprocess.Popen([PYTHON_EXEC, TRACKER_SCRIPT], start_new_session=True)

if __name__ == "__main__":
    main()

    main()
