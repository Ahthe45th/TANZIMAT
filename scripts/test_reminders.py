#!/home/mehmet/miniconda3/envs/idris/bin/python
import json
import subprocess
import os

REMINDERS_FILE = "/home/mehmet/Proyectos/TANZIMAT/reminders.json"
DISPLAY_SCRIPT = "/home/mehmet/Proyectos/TANZIMAT/display_reminder.py"

def load_reminders():
    if not os.path.exists(REMINDERS_FILE):
        return []
    with open(REMINDERS_FILE, 'r') as f:
        return json.load(f)

def rofi_select(prompt, options):
    rofi_process = subprocess.Popen(
        ['rofi', '-dmenu', '-p', prompt],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    stdout, _ = rofi_process.communicate('\n'.join(options))
    return stdout.strip()

def main():
    reminders = load_reminders()
    
    reminders_by_label = {}
    for reminder in reminders:
        label = reminder.get('label', 'Uncategorized')
        if label not in reminders_by_label:
            reminders_by_label[label] = []
        reminders_by_label[label].append(reminder)

    labels = list(reminders_by_label.keys())
    selected_label = rofi_select("Select a label", labels)

    if not selected_label:
        return

    selected_reminders = reminders_by_label[selected_label]
    
    reminder_descriptions = [f"{r.get('time', 'No time')} - {os.path.basename(r.get('file', 'No file'))}" for r in selected_reminders]
    selected_description = rofi_select("Select a reminder", reminder_descriptions)

    if not selected_description:
        return

    selected_reminder = None
    for r in selected_reminders:
        if f"{r.get('time', 'No time')} - {os.path.basename(r.get('file', 'No file'))}" == selected_description:
            selected_reminder = r
            break
    
    if not selected_reminder:
        return
        
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
            print(f"Error: Reminder file not found: {reminder_file}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    if post_command:
        print(f"Executing post-command: {post_command}")
        subprocess.run(post_command, shell=True)

if __name__ == "__main__":
    main()