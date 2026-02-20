#!/usr/bin/env python3

import subprocess
import datetime
import os

# Set DISPLAY environment variable for rofi
os.environ['DISPLAY'] = ':0'

# Define the questions
questions = [
    "What’s one thing I’m grateful for today?",
    "What’s one thing I struggled with today?",
    "What’s one thing I want to do better tomorrow?"
]

answers = []

# Ask each question using rofi and collect answers
for i, question in enumerate(questions):
    try:
        # Use rofi -dmenu for input
        rofi_command = ["rofi", "-dmenu", "-p", question]
        result = subprocess.run(rofi_command, capture_output=True, text=True, check=True)
        answer = result.stdout.strip()
        answers.append(f"{i+1}. {question}\n   {answer}")
    except subprocess.CalledProcessError as e:
        print(f"Rofi command failed: {e}")
        print(f"Stderr: {e.stderr}")
        answers.append(f"{i+1}. {question}\n   (No answer provided or error occurred)")
    except FileNotFoundError:
        print("Rofi not found. Please ensure rofi is installed and in your PATH.")
        answers.append(f"{i+1}. {question}\n   (Rofi not found)")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        answers.append(f"{i+1}. {question}\n   (Error: {e})")

# Get today's date for the filename
today_date = datetime.date.today().strftime("%Y-%m-%d")
filename = f"{today_date}.md"
file_path = f"/home/mehmet/Proyectos/TANZIMAT/NAFSIYYAH/Resources/{filename}"

# Format the answers into Markdown
markdown_content = f"# Shadow Work - {today_date}\n\n"
markdown_content += "\n\n".join(answers)
markdown_content += "\n" # Add a newline at the end

# Ensure the directory exists
os.makedirs(os.path.dirname(file_path), exist_ok=True)

# Save the result to the Markdown file and send notification
try:
    with open(file_path, "w") as f:
        f.write(markdown_content)
    message = f"Shadow work saved to {file_path}"
    print(message)
    subprocess.run(["notify-send", "Shadow Work", message])
except IOError as e:
    error_message = f"Error writing to file {file_path}: {e}"
    print(error_message)
    subprocess.run(["notify-send", "Shadow Work Error", error_message])
except Exception as e:
    error_message = f"An unexpected error occurred during file saving: {e}"
    print(error_message)
    subprocess.run(["notify-send", "Shadow Work Error", error_message])
