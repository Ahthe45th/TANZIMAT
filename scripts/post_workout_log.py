#!/usr/bin/env python3

import datetime
import os
import json
import re
import sys

# Get the absolute path of the directory containing THIS script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Add it to the Python path so we can import our custom utilities
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

# Import our shared GUI utilities
import gui_utils

QUESTIONS_FILE = os.path.join(SCRIPT_DIR, 'post_workout_log_questions.json')
REFLECTIONS_DIR = "/home/mehmet/Proyectos/TANZIMAT/NAFSIYYAH/Reflections"

HEADER_TITLE = "Post Workout Log"
NOTIFY_TITLE = "Post Workout Log"
PREFIX = "post_workout_log"

def read_existing_answers(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as f:
        content = f.read()
    pattern = r"### (.*?)\n(.*?)(?=\n### |\Z)"
    matches = re.findall(pattern, content, re.DOTALL)
    return {q.strip(): a.strip() for q, a in matches}

def save_answers(file_path, date_str, answers_dict, questions_order):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    lines = [f"# {HEADER_TITLE} - {date_str}\n"]
    for q in questions_order:
        if q in answers_dict:
            lines.append(f"### {q}")
            lines.append(answers_dict[q] + "\n")
    for q, a in answers_dict.items():
        if q not in questions_order:
            lines.append(f"### {q}")
            lines.append(a + "\n")
    with open(file_path, "w") as f:
        f.write("\n".join(lines))

def main():
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            questions = json.load(f)
    except Exception:
        gui_utils.notify("Error", f"Failed to load questions from {QUESTIONS_FILE}")
        return

    today_date = datetime.date.today().strftime("%Y-%m-%d")
    file_path = os.path.join(REFLECTIONS_DIR, f"{PREFIX}_{today_date}.md")
    existing_answers = read_existing_answers(file_path)

    questions_to_ask = [q for q in questions if q not in existing_answers]

    if not questions_to_ask:
        gui_utils.notify(NOTIFY_TITLE, "All questions already answered.")
        return

    new_answers = {}
    for question in questions_to_ask:
        # Use our shared utility!
        answer = gui_utils.get_rofi_input(f"{NOTIFY_TITLE}: {question}")
        if answer:
            new_answers[question] = answer
        else:
            # If user presses Esc or leaves it blank, stop or skip
            break

    if new_answers:
        existing_answers.update(new_answers)
        save_answers(file_path, today_date, existing_answers, questions)
        gui_utils.notify(NOTIFY_TITLE, f"Log updated at {today_date}")

if __name__ == "__main__":
    main()
