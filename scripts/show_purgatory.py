import requests
import subprocess
import os
import random
import string
from dotenv import load_dotenv
import logging

load_dotenv('tanzimat.env')

# --- LOGGING CONFIGURATION ---
script_dir = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(script_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "show_purgatory.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Starting show_purgatory.py script.")

def notify(message):
    subprocess.run(['notify-send', '[Purgatory]', message])
    logging.info(f"Notification: {message}")

def show_rofi_menu(options, prompt="Select an option:"):
    logging.info(f"Displaying Rofi menu with prompt: {prompt}")
    try:
        result = subprocess.run(
            ["rofi", "-dmenu", "-p", prompt],
            input="\n".join(options),
            capture_output=True,
            text=True,
            check=True
        )
        logging.info(f"Rofi menu choice: {result.stdout.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Rofi command failed: {e}")
        notify(f"Error with Rofi: {e}")
        return ""

def handle_activation(email):
    logging.info(f"Handling activation for email: {email}")
    try:
        response = requests.post("https://expatelitesingles.com/api/sirri_api/activate_user", json={'email': email})
        response.raise_for_status()
        notify(f"User {email} activated successfully.")
        logging.info(f"User {email} activated successfully.")
    except requests.exceptions.RequestException as e:
        notify(f"Failed to activate user {email}: {e}")
        logging.error(f"Failed to activate user {email}: {e}")

def handle_image_upload(email):
    logging.info(f"Handling image upload for email: {email}")
    # This part needs to be implemented based on how images are picked and uploaded
    # For now, let's just notify that it's not fully implemented
    notify("Image upload functionality not fully implemented yet.")
    logging.warning("Image upload functionality not fully implemented yet.")

def main():
    try:
        response = requests.get("https://staging.expatelitesingles.com/api/sirri_api/get_purgatory")
        response.raise_for_status()
        data = response.json()
        logging.info("Successfully fetched purgatory data.")

        if "acc" in data and data["acc"]:
            options = [f"{item['EMAIL']}" for item in data["acc"]]
            chosen_email = show_rofi_menu(options, prompt="Choose an email:")
            if chosen_email:
                logging.info(f"Selected email: {chosen_email}")
                pic_response = requests.get(f"https://expatelitesingles.com/api/profilepic/1?EMAIL={chosen_email}")
                
                if pic_response.status_code == 200 and pic_response.content:
                    logging.info(f"Profile picture found for {chosen_email}.")
                    handle_activation(chosen_email)
                else:
                    logging.warning(f"No profile picture found for {chosen_email}. Status: {pic_response.status_code}")
                    choice = show_rofi_menu(["Continue Without Pic", "Pick an Image", "Quit"], prompt="No profile pic found. What to do?")
                    if choice == "Continue Without Pic":
                        handle_activation(chosen_email)
                    elif choice == "Pick an Image":
                        handle_image_upload(chosen_email)
                    else:
                        logging.info("User chose to quit or closed Rofi menu.")

        else:
            notify("No accounts found in purgatory.")
            logging.info("No accounts found in purgatory.")

    except requests.exceptions.RequestException as e:
        notify(f"Error fetching data: {e}")
        logging.error(f"Error fetching data: {e}")
    except (KeyError, TypeError) as e:
        notify(f"Error parsing response: {e}")
        logging.error(f"Error parsing response: {e}")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")
        notify(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
