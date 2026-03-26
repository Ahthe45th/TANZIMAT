#!/usr/bin/env python3

import datetime
import os
import json
import re
import sys
import calendar

# Get the absolute path of the directory containing THIS script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

import gui_utils

QUESTIONS_FILE = os.path.join(SCRIPT_DIR, 'monthly_checkin_questions.json')
REFLECTIONS_DIR = "/home/mehmet/Proyectos/TANZIMAT/NAFSIYYAH/Reflections"

HEADER_TITLE = "Monthly Check-in"
NOTIFY_TITLE = "Monthly Check-in"
PREFIX = "monthly_checkin"

def get_questions():
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def get_file_path():
    today = datetime.date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    last_date = datetime.date(today.year, today.month, last_day)
    date_str = last_date.strftime("%Y-%m-%d")
    filename = f"{PREFIX}_{date_str}.md"
    return os.path.join(REFLECTIONS_DIR, filename), date_str

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
    questions = get_questions()
    if not questions:
        gui_utils.notify("Error", f"No questions found in {QUESTIONS_FILE}")
        return

    file_path, date_str = get_file_path()
    existing_answers = read_existing_answers(file_path)

    menu_items = [f"{'[DONE] ' if q in existing_answers else '[ ] '}{q}" for q in questions]

    selected_raw = gui_utils.get_rofi_menu(f"Select {NOTIFY_TITLE} question:", menu_items)
    if not selected_raw:
        return
    
    selected_question = gui_utils.strip_status(selected_raw)
    initial_answer = existing_answers.get(selected_question, "")
    answer = gui_utils.get_rofi_input(f"Answer for: {selected_question}", initial_value=initial_answer)
    
    if answer is not None:
        existing_answers[selected_question] = answer
        save_answers(file_path, date_str, existing_answers, questions)
        gui_utils.notify(NOTIFY_TITLE, f"Answer for '{selected_question}' saved.")

if __name__ == "__main__":
    main()
