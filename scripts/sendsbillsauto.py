#!/usr/bin/env python3

import subprocess
import time
#import pytesseract
#from PIL import Image
import requests
import os
import shutil
from dotenv import load_dotenv
#from google.cloud import vision
import io
import glob
import logging
import datetime
import re
from datetime import date

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, 'tanzimat.env')

load_dotenv(env_path)

# --- LOGGING CONFIGURATION ---
LOG_DIR = os.path.join(script_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "sendsbillsauto.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Starting sendsbillsauto.py script.")

def find_text_coordinates(image_path, target_text, service_account_path):
    """
    Uses Google Cloud Vision to find the coordinates of a target word in an image.

    Returns a list of dictionaries with 'text' and 'box' (polygon of 4 (x, y) tuples)
    """
    logging.info(f"Finding text coordinates for '{target_text}' in {image_path} using Vision API.")
    client = vision.ImageAnnotatorClient.from_service_account_file(service_account_path)

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)

    if response.error.message:
        logging.error(f"Vision API error: {response.error.message}")
        raise Exception(f'API Error: {response.error.message}')

    results = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = ''.join([symbol.text for symbol in word.symbols])
                    if word_text.lower() == target_text.lower():
                        vertices = word.bounding_box.vertices
                        box = [(v.x, v.y) for v in vertices]
                        results.append({"text": word_text, "box": box})
    logging.info(f"Found {len(results)} matches for '{target_text}'.")
    return results

def format_bills(bills_string):
    """
    Formats a string of bill information into two sections: "BILLS" and "NEXT 7 DAYS".

    Args:
        bills_string: A multi-line string where each line represents a bill
                      with name, due date (DD/MM/YY), and amount.

    Returns:
        A formatted string with the bill information categorized.
    """
    output = "*BILLS*\n\n"
    output += bills_string
    output += "\n\n*NEXT 7 DAYS*\n\n"

    today = datetime.date.today() # Make this dynamic
    seven_days_from_now = today + datetime.timedelta(days=7)

    next_7_days_bills = []
    for line in bills_string.strip().split('\n'):
        if not line.strip(): # Skip empty lines
            continue
        try:
            # Regex to parse the line: Name DD/MM/YY - KSH Amount
            # This regex is more robust for multi-word names
            match = re.match(r"^(.*?)\s+(\d{2}/\d{2}/\d{2})\s+-\s+KSH\s+([\d,]+)$", line.strip())
            if not match:
                logging.warning(f"Line did not match expected format: {line}")
                continue

            name = match.group(1).strip()
            date_str = match.group(2)
            amount = match.group(3)

            day, month, year = map(int, date_str.split('/'))
            # Assuming years are in 20xx, adjust if necessary for 19xx
            bill_date = datetime.date(2000 + year, month, day)

            if today <= bill_date <= seven_days_from_now:
                formatted_date = bill_date.strftime('%a %b %d %Y')
                next_7_days_bills.append(f"{name} KSH {amount} - {formatted_date}")
        except (ValueError, IndexError, AttributeError) as e:
            logging.error(f"Could not parse line: {line} due to error: {e}")


    output += '\n'.join(next_7_days_bills)
    return output

# --- NOTIFY ---
def notify(message):
    subprocess.run(['notify-send', '[🟢 WhatsApp Bot]', message])
    logging.info(f"Notification: {message}")

# --- FUNCTIONS ---
def get_active_window_title():
    try:
        win_id = subprocess.check_output(["xdotool", "getactivewindow"]).decode().strip()
        win_name = subprocess.check_output(["xprop", "-id", win_id, "WM_NAME"]).decode()
        logging.info(f"Active window title: {win_name.strip()}")
        return win_name
    except Exception as e:
        logging.error(f"Failed to get window title: {e}")
        notify(f"❌ Failed to get window title: {e}")
        return ""

def cycle_tabs_until_whatsapp(max_tabs=10):
    logging.info("Cycling tabs until WhatsApp is found.")
    for i in range(max_tabs):
        subprocess.run(["xdotool", "key", "ctrl+Tab"])
        time.sleep(1)
        title = get_active_window_title()
        if "whatsapp" in title.lower():
            notify(f"✅ Found WhatsApp tab after {i+1} switches")
            logging.info(f"Found WhatsApp tab after {i+1} switches.")
            return True
    notify("❌ WhatsApp tab not found")
    logging.warning("WhatsApp tab not found after cycling.")
    return False

def click_whatsapp_or_cycle():
    notify("🔍 Trying to click WhatsApp...")
    logging.info("Attempting to click WhatsApp or cycle tabs.")
    screenshot()
    coords = find_text_coords("WhatsApp")
    if coords:
        subprocess.run(["xdotool", "mousemove", str(coords[0]), str(coords[1]), "click", "1"])
        notify("✅ Clicked WhatsApp via OCR")
        logging.info("Clicked WhatsApp via OCR.")
    else:
        notify("⚠️ WhatsApp text not found — falling back to tab switch...")
        logging.warning("WhatsApp text not found, falling back to tab switch.")
        # Focus window by clicking screen center
        screen_x = shutil.get_terminal_size().columns * 8 // 2
        screen_y = 500  # or set dynamically
        subprocess.run(["xdotool", "mousemove", str(screen_x), str(screen_y), "click", "1"])
        time.sleep(0.5)
        cycle_tabs_until_whatsapp()

def fetch_message():
    url = "https://n8n.tuongeechat.com/webhook/dc00ae57-d004-4f30-a9da-14fd6a632e3a"
    logging.info(f"Fetching message from {url}")
    try:
        r = requests.get(url)
        r.raise_for_status()
        message_data = r.json()["data"]
        logging.info("Message fetched successfully.")
        return format_bills(message_data)
    except Exception as e:
        notify("❌ Failed to fetch message")
        logging.error(f"Failed to fetch message: {e}")
        return "MESSAGE FAILED TO LOAD"

def set_clipboard(text):
    logging.info("Setting clipboard content.")
    subprocess.run(['/usr/bin/wl-copy'], input=text.encode('utf-8'))

def screenshot(path="/tmp/screen.png"):
    logging.info(f"Taking screenshot to {path}")
    subprocess.run(["scrot", path])
    return Image.open(path)

def find_text_coords(text, image_path="/tmp/screen.png"):
    logging.info(f"Finding text '{text}' in image {image_path}")
    # Try pytesseract first
    try:
        image = Image.open(image_path)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        for i, word in enumerate(data["text"]):
            if text.lower() in word.lower():
                x = data["left"][i] + data["width"][i] // 2
                y = data["top"][i] + data["height"][i] // 2
                logging.info(f"Found text '{text}' at ({x}, {y}) using Tesseract.")
                return (x, y)
    except ImportError:
        logging.warning("Pytesseract or PIL not installed. Cannot use Tesseract fallback.")
    except Exception as e:
        logging.error(f"Error using Tesseract for OCR: {e}")

    # Fallback to Google Cloud Vision if pytesseract fails
    script_dir = os.path.dirname(os.path.abspath(__file__))
    service_account_files = glob.glob(os.path.join(script_dir, "pimpting*.json"))

    if service_account_files:
        service_account_path = service_account_files[0]
        try:
            vision_results = find_text_coordinates(image_path, text, service_account_path)
            if vision_results:
                # Assuming we take the first match
                box = vision_results[0]['box']
                center_x = sum([pt[0] for pt in box]) // 4
                center_y = sum([pt[1] for pt in box]) // 4
                logging.info(f"Found text '{text}' at ({center_x}, {center_y}) using Vision API.")
                return (center_x, center_y)
        except Exception as e:
            logging.error(f"Vision API failed: {e}")
            notify(f"Vision API failed: {e}")

    logging.warning(f"Text '{text}' not found in image {image_path}.")
    return None

def click_text(text):
    logging.info(f"Attempting to click text: {text}")
    screenshot()
    coords = find_text_coords(text)
    if coords:
        x, y = coords
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"])
        notify(f"✅ Clicked '{text}'")
        logging.info(f"Clicked text: {text}")
        time.sleep(0.6)
    else:
        notify(f"⚠️ Text '{text}' not found on screen.")
        logging.warning(f"Text '{text}' not found on screen.")

def paste_clipboard():
    logging.info("Pasting clipboard content.")
    os.environ["DISPLAY"] = ":1"
    subprocess.run(["/usr/bin/wl-paste"])
    notify("✅ Message pasted")
    logging.info("Message pasted and sent.")

# --- MAIN FLOW ---
if __name__ == "__main__":
    try:
        # First, run the script to update bills on Nextcloud
        notify("🔄 Updating bills on Nextcloud...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        update_script_path = os.path.join(script_dir, "update_nextcloud_bills.sh")
        subprocess.run(["bash", update_script_path], check=True)
        logging.info("Successfully ran update_nextcloud_bills.sh.")

        notify("🚀 Running WhatsApp bot...")
        logging.info("Running WhatsApp bot.")

        # 1. Get message
        message = fetch_message()
        notify("📥 Message fetched")
        logging.info("Message fetched.")
        print(message)
        # Send HTTP POST request
        try:
            current_date_str = date.today().isoformat()
            subject = f"Bills for {current_date_str}"
            payload = {
                            "SUBJECT": subject,
                            "BODY": message, "extras": "abushuriya@gmail.com,dchege411@gmail.com"
            }
            webhook_url = "https://n8n.tuongeechat.com/webhook/ddf10b7c-7764-4d25-8459-6cef88d2041f"
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status() # Raise an exception for HTTP errors
            logging.info(f"Successfully sent POST request for {subject}. Status Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send POST request for {subject}: {e}")
            notify("Sending email of bills failed brother. Check the logs.")

        # 2. Set clipboard
        #set_clipboard(message)
        #notify("📋 Clipboard set")
        #logging.info("Clipboard set.")

        # 3. Focus desktop 3
        #subprocess.run(["bspc", "desktop", "-f", "^3"])
        #time.sleep(1)
        #notify("🖥️ Switched to desktop 3")
        #logging.info("Switched to desktop 3.")

        # 4. Click WhatsApp
        #click_whatsapp_or_cycle()

        # 5. Click BILLS
        #click_text("BILLS")

        # 6. Paste message and send
        logging.info("sendsbillsauto.py script finished successfully.")
    except Exception as e:
        logging.critical(f"Script failed: {e}")
        notify(f"❌ Script failed: {e}")
