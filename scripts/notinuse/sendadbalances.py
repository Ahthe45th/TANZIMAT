#!/usr/bin/env python3
import os
import subprocess
import time
import base64
from openai import OpenAI
from PIL import Image
import pytesseract
import shutil 
from dotenv import load_dotenv
from google.cloud import vision
import io
import glob
import logging

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, 'tanzimat.env')

load_dotenv(env_path)

# --- LOGGING CONFIGURATION ---
LOG_DIR = os.path.join(script_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "sendadbalances.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Starting sendadbalances.py script.")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# --- PATHS ---
BASE_DIR = os.path.expanduser("~/firefox_shots")
IMAGES = [
    os.path.join(BASE_DIR, "2_desktop3_after_scroll.png"),
    os.path.join(BASE_DIR, "3_desktop2_after_scroll.png")
]

# --- FUNCTIONS ---
def notify(msg):
    subprocess.run(["notify-send", "[Vision→WhatsApp]", msg])
    logging.info(f"Notification: {msg}")

def summarize_image(path):
    notify(f"📤 Sending {os.path.basename(path)} to OpenAI")
    logging.info(f"Summarizing image: {path}")
    with open(path, "rb") as f:
        b64_img = base64.b64encode(f.read()).decode("utf-8")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Extract ad account name, current funds, and recent charges from this screenshot."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Summarize the ad billing screen into this format:\n\nAccount: [Name]\nFunds: [KSh Amount]\nRecent Charges:\n- Item 1\n- Item 2"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
                ]}
            ],
            max_tokens=300
        )
        summary = response.choices[0].message.content.strip()
        logging.info(f"Image summary generated for {path}")
        return summary
    except Exception as e:
        logging.error(f"Error summarizing image {path}: {e}")
        notify(f"❌ Error summarizing image: {e}")
        return ""

def set_clipboard(text):
    logging.info("Setting clipboard content.")
    subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'))

def screenshot(path="/tmp/_screen.png"):
    logging.info(f"Taking screenshot to {path}")
    subprocess.run(["scrot", path])
    return path

def find_text_coords(text, image_path='/tmp/_screen.png'):
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

def click_text(text):
    logging.info(f"Attempting to click text: {text}")
    img_path = screenshot()
    coords = find_text_coords(text, img_path)
    if coords:
        subprocess.run(["xdotool", "mousemove", str(coords[0]), str(coords[1]), "click", "1"])
        time.sleep(0.6)
        logging.info(f"Clicked text: {text}")
    else:
        notify(f"❌ Couldn’t find text: {text}")
        logging.warning(f"Could not find text: {text}")

def paste_clipboard():
    logging.info("Pasting clipboard content.")
    subprocess.run(["xdotool", "key", "ctrl+shift+v"])
    time.sleep(0.2)
    subprocess.run(["xdotool", "key", "Return"])

# --- MAIN FLOW ---
if __name__ == "__main__":
    try:
        notify("🧠 Analyzing billing screenshots...")
        logging.info("Analyzing billing screenshots.")

        summaries = [summarize_image(img) for img in IMAGES]
        final_message = "*BILLING REPORT*\n\n" + "\n\n---\n\n".join(summaries)
        set_clipboard(final_message)
        notify("📋 Billing summary copied to clipboard")
        logging.info("Billing summary copied to clipboard.")

        # --- SEND TO WHATSAPP ---
        subprocess.run(["bspc", "desktop", "-f", "^3"])
        time.sleep(1)
        logging.info("Switched to desktop 3.")
        click_whatsapp_or_cycle()
        click_text("(You)")
        paste_clipboard()
        notify("✅ Billing report sent via WhatsApp")
        logging.info("Billing report sent via WhatsApp. Script finished successfully.")
    except Exception as e:
        logging.critical(f"Script failed: {e}")
        notify(f"❌ Script failed: {e}")
