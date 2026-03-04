#!/home/mehmet/miniconda3/envs/idris/bin/python
import json
import time
import datetime
import subprocess
import os
import logging
import requests

REMINDERS_FILE = "/home/mehmet/Proyectos/TANZIMAT/reminders.json"
DISPLAY_SCRIPT = "/home/mehmet/Proyectos/TANZIMAT/display_reminder.py"
LOG_FILE = "/home/mehmet/Proyectos/TANZIMAT/reminder_service.log"

def load_reminders():
    if not os.path.exists(REMINDERS_FILE):
        return []
    with open(REMINDERS_FILE, 'r') as f:
        return json.load(f)

def save_reminders(reminders):
    with open(REMINDERS_FILE, 'w') as f:
        json.dump(reminders, f, indent=4)

def check_reminders():
    reminders = load_reminders()
    now = datetime.datetime.now()
    current_time_str = now.strftime("%H:%M")
    current_date_str = now.strftime("%Y-%m-%d")
    current_day_of_week = now.weekday() # Monday is 0 and Sunday is 6
    reminder_triggered = False

    for reminder in reminders:
        reminder_time_str = reminder['time']
        last_triggered_date = reminder.get('last_triggered')
        allowed_days = reminder.get('days')
        days_of_month = reminder.get('days_of_month')
        repeat_days = reminder.get('repeat_days')
        start_date = reminder.get('start_date')
        pre_command = reminder.get('pre_command')
        post_command = reminder.get('post_command')
        no_notif = reminder.get('skip_notification', False)

        # Check if the reminder should be triggered based on the day of the week
        if allowed_days and current_day_of_week not in allowed_days:
            continue

        # Check if the reminder should be triggered based on the day of the month
        if days_of_month and now.day not in days_of_month:
            continue

        # Check if the reminder should be triggered based on repeat_days and start_date
        if repeat_days and start_date:
            try:
                start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                if now >= start_date_obj:
                    delta_days = (now - start_date_obj).days
                    if delta_days % repeat_days != 0:
                        continue
            except ValueError:
                logging.error(f"Invalid start_date format for reminder: {reminder['file']}. Expected YYYY-MM-DD.")
                continue

        if reminder_time_str <= current_time_str and (last_triggered_date is None or last_triggered_date < current_date_str):
            logging.info(f"Reminder triggered for {reminder['file']} at {reminder['time']}")
            reminder_triggered = True
            try:
                if pre_command:
                    logging.info(f"Executing pre-command: {pre_command}")
                    env = os.environ.copy()
                    #env['DISPLAY'] = ':1'
                    pre_result = subprocess.run(pre_command, shell=True, capture_output=True, text=True, env=env)
                    logging.info(f"Pre-command stdout: {pre_result.stdout}")
                    if pre_result.stderr:
                        logging.error(f"Pre-command stderr: {pre_result.stderr}")

                with open(reminder['file'], 'r') as f:
                    file_content = f.read()

                # Call the graphical display script
                if no_notif:
                    logging.info("SKip notif was enabled")
                    returncode = 0
                else:
                    logging.info("Skip notif was not enabled")
                    result = subprocess.run(["/home/mehmet/miniconda3/envs/idris/bin/python", DISPLAY_SCRIPT, file_content], capture_output=True, text=True)
                    returncode = result.returncode
                
                if returncode == 0: # Acknowledged
                    logging.info(f"Reminder for {reminder['file']} acknowledged.")
                    reminder['last_triggered'] = current_date_str
                    save_reminders(reminders)

                    if post_command:
                        logging.info(f"Executing post-command: {post_command}")
                        env = os.environ.copy()
                        #env['DISPLAY'] = ':1'
                        post_result = subprocess.run(post_command, shell=True, capture_output=True, text=True, env=env)
                        logging.info(f"Post-command stdout: {post_result.stdout}")
                        if post_result.stderr:
                            logging.error(f"Post-command stderr: {post_result.stderr}")

                    # Send HTTP POST request
                    #try:
                    #    filename_end = os.path.basename(reminder['file'])
                    #    subject = f"{filename_end} reminder {current_date_str}"
                    #    payload = {
                    #        "SUBJECT": subject,
                    ##        "BODY": file_content
                    #    }
                    #    webhook_url = "https://n8n.tuongeechat.com/webhook/ddf10b7c-7764-4d25-8459-6cef88d2041f"
                    #    response = requests.post(webhook_url, json=payload)
                    #    response.raise_for_status() # Raise an exception for HTTP errors
                    #    logging.info(f"Successfully sent POST request for {subject}. Status Code: {response.status_code}")
                    #except requests.exceptions.RequestException as e:
                    #    logging.error(f"Failed to send POST request for {subject}: {e}")

                else:
                    logging.warning(f"Reminder for {reminder['file']} not acknowledged (script exited with {result.returncode}).")
                    logging.warning(f"Stderr: {result.stderr}")

            except FileNotFoundError:
                logging.error(f"Error: Reminder file not found: {reminder['file']}")
            except Exception as e:
                logging.exception(f"An unexpected error occurred: {e}")
    
    if not reminder_triggered:
        logging.info("No reminders to launch at this time.")

def main():
    logging.basicConfig(filename=LOG_FILE, 
                        level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Reminder service started.")
    while True:
        check_reminders()
        time.sleep(60) # Check every minute

if __name__ == "__main__":
    main()
