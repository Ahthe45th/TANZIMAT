import json
import sys
import os
import subprocess

REMINDERS_FILE = "/home/mehmet/Proyectos/TANZIMAT/reminders.json"
DISPLAY_SCRIPT = "/home/mehmet/Proyectos/TANZIMAT/display_reminder.py"

def show_reminder(label):
    if not os.path.exists(REMINDERS_FILE):
        print(f"Error: Reminders file not found at {REMINDERS_FILE}")
        return

    with open(REMINDERS_FILE, 'r') as f:
        reminders = json.load(f)

    found_reminder = None
    for reminder in reminders:
        if reminder.get('label') == label:
            found_reminder = reminder
            break

    if found_reminder:
        pre_command = found_reminder.get('pre_command')
        post_command = found_reminder.get('post_command')
        
        env = os.environ.copy()
        env['DISPLAY'] = ':0'

        if pre_command:
            print(f"Executing pre-command: {pre_command}")
            pre_result = subprocess.run(pre_command, shell=True, capture_output=True, text=True, env=env)
            print(f"Pre-command stdout: {pre_result.stdout}")
            if pre_result.stderr:
                print(f"Pre-command stderr: {pre_result.stderr}")

        reminder_file_path = found_reminder.get('file')
        if reminder_file_path and os.path.exists(reminder_file_path):
            with open(reminder_file_path, 'r') as f:
                content = f.read()
            
            try:
                result = subprocess.run(
                    ["/home/mehmet/miniconda3/envs/idris/bin/python", DISPLAY_SCRIPT, content],
                    check=True,
                    env=env,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0: # Acknowledged
                    if post_command:
                        print(f"Executing post-command: {post_command}")
                        post_result = subprocess.run(post_command, shell=True, capture_output=True, text=True, env=env)
                        print(f"Post-command stdout: {post_result.stdout}")
                        if post_result.stderr:
                            print(f"Post-command stderr: {post_result.stderr}")

            except subprocess.CalledProcessError as e:
                print(f"Error displaying reminder: {e}")
        else:
            print(f"Error: Reminder file not found for label '{label}' at {reminder_file_path}")
    else:
        print(f"Error: No reminder found with label '{label}'")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python show_reminder_by_label.py <label>")
        sys.exit(1)
    
    reminder_label = sys.argv[1]
    show_reminder(reminder_label)
