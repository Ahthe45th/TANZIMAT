import json
import argparse
import os
from datetime import datetime

REMINDERS_FILE = "/home/mehmet/Proyectos/TANZIMAT/reminders.json"

def _load_reminders(path: str):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            if isinstance(data, list):
                return data
            # If someone accidentally wrote an object instead of a list, fail safely
            return []
    except (json.JSONDecodeError, OSError):
        # Corrupt/unreadable file: fail safely rather than crash
        return []

def _save_reminders(path: str, reminders):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(reminders, f, indent=4)

def add_reminder(args):
    reminders = _load_reminders(REMINDERS_FILE)

    # Normalize label (optional but recommended)
    new_label = args.label.strip()

    new_reminder = {
        "time": args.time,
        "file": args.file,
        "label": new_label,
        "last_triggered": None,
        "days": args.days,
        "days_of_month": args.days_of_month,
        "repeat_days": args.repeat_days,
        "start_date": args.start_date,
        "pre_command": args.pre_command,
        "post_command": args.post_command,
        "one_off": args.one_off
    }

    # Remove any existing reminder with the same label (new one wins)
    before = len(reminders)
    reminders = [r for r in reminders if (r.get("label") or "").strip() != new_label]
    removed = before - len(reminders)

    reminders.append(new_reminder)
    _save_reminders(REMINDERS_FILE, reminders)

    if removed:
        print(f"Reminder '{new_label}' updated successfully (replaced {removed} existing).")
    else:
        print(f"Reminder '{new_label}' added successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a new reminder.")
    parser.add_argument("--time", required=True, help="Time for the reminder (HH:MM).")
    parser.add_argument("--file", required=True, help="Absolute path to the reminder file.")
    parser.add_argument("--label", required=True, help="A unique label for the reminder.")
    parser.add_argument("--days", nargs='*', type=int, help="Days of the week (0=Monday, 6=Sunday).")
    parser.add_argument("--days-of-month", nargs='*', type=int, help="Days of the month.")
    parser.add_argument("--repeat-days", type=int, help="Repeat every X days.")
    parser.add_argument("--start-date", help="Start date for repeating reminders (YYYY-MM-DD).")
    parser.add_argument("--pre-command", help="Command to execute before the reminder.")
    parser.add_argument("--post-command", help="Command to execute after the reminder.")
    parser.add_argument("--one-off", action="store_true", help="Remove reminder after acknowledged display.")

    args = parser.parse_args()

    if args.start_date:
        try:
            datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            print("Error: Invalid start_date format. Please use YYYY-MM-DD.")
            exit(1)

    add_reminder(args)
