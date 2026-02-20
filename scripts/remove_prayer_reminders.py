
import json
import os
import subprocess

REMINDERS_FILE = "/home/mehmet/Proyectos/TANZIMAT/reminders.json"

def remove_prayer_reminders():
    if not os.path.exists(REMINDERS_FILE):
        print("Reminders file not found.")
        return

    with open(REMINDERS_FILE, 'r') as f:
        reminders = json.load(f)

    # Filter out prayer-related reminders
    original_count = len(reminders)
    reminders = [r for r in reminders if "Prayer" not in r.get("label", "")]
    new_count = len(reminders)

    with open(REMINDERS_FILE, 'w') as f:
        json.dump(reminders, f, indent=4)

    print(f"Removed {original_count - new_count} prayer reminders.")

if __name__ == "__main__":
    try:
        remove_prayer_reminders()
        subprocess.run(["bash", "-c", "DISPLAY=:0 notify-send 'Prayer Reminders Removed' 'The prayer reminders have been successfully removed.'"])
    except Exception as e:
        subprocess.run(["bash", "-c", f"DISPLAY=:0 notify-send 'Error Removing Prayer Reminders' '{e}'"])
