#!/home/mehmet/miniconda3/envs/idris/bin/python
import json
import subprocess
import os
import sys

# Get the absolute path of the directory containing THIS script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

import gui_utils

REMINDERS_FILE = "/home/mehmet/Proyectos/TANZIMAT/reminders.json"
DISPLAY_SCRIPT = "/home/mehmet/Proyectos/TANZIMAT/display_reminder.py"

def load_reminders():
    if not os.path.exists(REMINDERS_FILE):
        return []
    try:
        with open(REMINDERS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def main():
    reminders = load_reminders()
    if not reminders:
        gui_utils.notify("Test Reminders", "No reminders found.")
        return
    
    reminders_by_label = {}
    for reminder in reminders:
        label = reminder.get('label', 'Uncategorized')
        reminders_by_label.setdefault(label, []).append(reminder)

    labels = sorted(list(reminders_by_label.keys()))
    selected_label = gui_utils.get_rofi_menu("Select a label", labels)

    if not selected_label:
        return

    selected_reminders = reminders_by_label[selected_label]
    
    # Use index to handle potential duplicate descriptions safely
    reminder_descriptions = [f"{r.get('time', 'No time')} - {os.path.basename(r.get('file', 'No file'))}" for r in selected_reminders]
    idx = gui_utils.get_rofi_menu("Select a reminder", reminder_descriptions, index=True)

    if idx is None:
        return

    selected_reminder = selected_reminders[idx]
        
    pre_command = selected_reminder.get('pre_command')
    post_command = selected_reminder.get('post_command')
    reminder_file = selected_reminder.get('file')

    if pre_command:
        print(f"Executing pre-command: {pre_command}")
        subprocess.run(pre_command, shell=True)

    if reminder_file:
        try:
            with open(reminder_file, 'r') as f:
                file_content = f.read()
            
            subprocess.run(["/home/mehmet/miniconda3/envs/idris/bin/python", DISPLAY_SCRIPT, file_content])

        except FileNotFoundError:
            gui_utils.notify("Error", f"Reminder file not found: {reminder_file}")
        except Exception as e:
            gui_utils.notify("Error", f"An unexpected error occurred: {e}")

    if post_command:
        print(f"Executing post-command: {post_command}")
        subprocess.run(post_command, shell=True)

if __name__ == "__main__":
    main()
