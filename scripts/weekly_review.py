#!/usr/bin/env python3

import datetime
import os
import json
import re
import sys

# Get the absolute path of the directory containing THIS script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

import gui_utils

QUESTIONS_FILE = os.path.join(SCRIPT_DIR, 'weekly_review_questions.json')
REFLECTIONS_DIR = "/home/mehmet/Proyectos/TANZIMAT/NAFSIYYAH/Reflections"

HEADER_TITLE = "Weekly Review"
NOTIFY_TITLE = "Weekly Review"
PREFIX = "weekly_review"

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

    today = datetime.date.today()
    days_until_sunday = (6 - today.weekday()) % 7
    sunday = today + datetime.timedelta(days=days_until_sunday)
    date_str = sunday.strftime("%Y-%m-%d")

    file_path = os.path.join(REFLECTIONS_DIR, f"{PREFIX}_{date_str}.md")
    existing_answers = read_existing_answers(file_path)

    questions_to_ask = [q for q in questions if q not in existing_answers]

    if not questions_to_ask:
        gui_utils.notify(NOTIFY_TITLE, "All questions already answered.")
        return

    new_answers = {}
    for question in questions_to_ask:
        answer = gui_utils.get_rofi_input(f"{NOTIFY_TITLE}: {question}")
        if answer:
            new_answers[question] = answer
        else:
            break

    if new_answers:
        existing_answers.update(new_answers)
        save_answers(file_path, date_str, existing_answers, questions)
        gui_utils.notify(NOTIFY_TITLE, f"Weekly Review updated for {date_str}")

if __name__ == "__main__":
    main()
