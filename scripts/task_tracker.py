#!/home/mehmet/miniconda3/envs/idris/bin/python3
import time
import os
import sys
from datetime import datetime

# Get the absolute path of the directory containing THIS script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from gui_utils import get_rofi_input, get_rofi_menu, notify

LOG_FILE = os.path.join(SCRIPT_DIR, "logs/task_tracking.log")
CURRENT_TASK_FILE = "/tmp/current_task.txt"

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def set_current_task(task_name):
    with open(CURRENT_TASK_FILE, "w") as f:
        f.write(task_name)

def clear_current_task():
    if os.path.exists(CURRENT_TASK_FILE):
        os.remove(CURRENT_TASK_FILE)

def main():
    while True:
        task = get_rofi_input("What is the current task?")
        if not task:
            break
        
        minutes_str = get_rofi_input("How long is it expected to take (minutes)?")
        if not minutes_str or not minutes_str.isdigit():
            minutes = 0
        else:
            minutes = int(minutes_str)
        
        log_event(f"START - Task: {task}, Est: {minutes}m")
        set_current_task(task)
        
        while True:
            if minutes > 0:
                time.sleep(minutes * 60)
            
            notify("Task Timer", f"Time is up for: {task}")
            
            choice = get_rofi_menu(f"Is the task '{task}' completed?", ["Yes", "No"])
            
            if choice is None: # Rofi cancelled
                # We can either ask again or assume not finished.
                # Let's ask again in the next loop.
                continue

            if choice == "Yes":
                log_event(f"COMPLETE - Task: {task}")
                clear_current_task()
                break
            else:
                extra_str = get_rofi_input("How many more minutes are required?")
                if extra_str is None:
                    minutes = 5 # Default if cancelled, will ask again soon
                elif not extra_str.isdigit():
                    minutes = 1 # Default if invalid
                else:
                    minutes = int(extra_str)
                log_event(f"EXTENSION - Task: {task}, Extra: {minutes}m")

if __name__ == "__main__":
    main()
