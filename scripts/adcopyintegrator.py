import os
import subprocess
import json
from dotenv import load_dotenv
import logging

# --- Basic Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, 'tanzimat.env')
load_dotenv(env_path)

# --- Logging Configuration ---
LOG_DIR = os.path.join(script_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "adcopyintegrator.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_notification(message):
    """Sends a desktop notification."""
    try:
        env = os.environ.copy()
        env['DISPLAY'] = ':0'
        subprocess.run(['notify-send', message], check=True, env=env)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"notify-send command failed: {e}")
        print(message) # Fallback to print if notify-send fails

def get_input_from_zenity(prompt):
    """
    Gets multiline text input from the user using Zenity.
    """
    try:
        prompt_message = f"{prompt}\n\nMake sure to delete everything here before inputting your own data."
        result = subprocess.run(
            ['zenity', '--text-info', '--editable', '--title', 'Ad Copy Input', '--width', '400', '--height', '300', '--filename=/dev/stdin'],
            input=prompt_message,
            capture_output=True,
            text=True,
            check=True  # Raise an exception if zenity fails
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"Zenity command failed: {e}")
        # Fallback to console input if zenity is not available or fails
        print(prompt)
        return input()


def process_with_fabric(text):
    """
    Processes the given text using the fabric tool with the 'adcopyintegrator' pattern.
    """
    try:
        command = [
            '/home/mehmet/.local/bin/fabric',
            '-m',
            'z-ai/glm-4.6',
            '--pattern',
            'adcopyintegrator'
        ]
        result = subprocess.run(
            command,
            input=text,
            capture_output=True,
            text=True,
            check=True # Raise an exception if fabric fails
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"Fabric command failed: {e}")
        return f"Error processing text with fabric: {e}"


def copy_to_clipboard(text):
    """
    Copies the given text to the system clipboard using xclip.
    """
    try:
        subprocess.run(
            ['/usr/bin/wl-copy'],
            input=text,
            text=True,
            check=True # Raise an exception if xclip fails
        )
        send_notification("Result copied to clipboard.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"xclip command failed: {e}")
        send_notification(f"Could not copy to clipboard. Error: {e}")
        print("Here is the result instead:")
        print(text)

def main():
    """
    Main function to get input, process it, and copy the result to the clipboard.
    """
    # 1. Get input from Zenity
    user_input = get_input_from_zenity("Please paste the ad copy data:")

    if not user_input:
        send_notification("No input provided. Exiting.")
        return

    # 2. Process the input with the fabric tool
    processed_result = process_with_fabric(user_input)

    if processed_result.startswith("Error"):
        send_notification(processed_result)
        return

    # 3. Copy the result to the clipboard
    copy_to_clipboard(processed_result)

if __name__ == '__main__':
    main()
