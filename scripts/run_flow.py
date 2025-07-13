#!/usr/bin/env python3
import json
import subprocess
import time
import uuid
import os
from google.cloud import vision
import io
import glob
from pathlib import Path
from typing import List, Dict
import logging

SCRIPT_DIR = Path(__file__).resolve().parent
FLOW_DIR = SCRIPT_DIR.parent / "flows"

# --- LOGGING CONFIGURATION ---
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "run_flow.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def rofi(prompt: str, options: List[str]) -> str:
    logging.info(f"Rofi prompt: {prompt}, options: {options}")
    joined = "\n".join(options)
    result = subprocess.run(
        ["rofi", "-dmenu", "-p", prompt],
        input=joined,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        logging.error(f"Rofi command failed with error: {result.stderr.decode().strip()}")
        return ""
    logging.info(f"Rofi selection: {result.stdout.strip()}")
    return result.stdout.strip()


def click_coords(x: int, y: int):
    logging.info(f"Clicking coordinates: ({x}, {y})")
    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"])


def run_action(action: Dict):
    name = action.get("action")
    logging.info(f"Running action: {name} with data: {action}")
    if name == "coordinate_click":
        click_coords(action["x"], action["y"])
    elif name == "window_switch":
        subprocess.run(["bspc", "desktop", "-f", f"^{action['desktop']}"])
        logging.info(f"Switched to desktop: {action['desktop']}")
    elif name == "text_finder":
        text = action["text"]
        img = f"/tmp/flow_screen_{uuid.uuid4()}.png"
        subprocess.run(["scrot", img])
        coords = find_text_coords(text, img)
        if coords:
            click_coords(*coords)
            logging.info(f"Found and clicked text: '{text}'")
        else:
            logging.warning(f"Text '{text}' not found.")
        os.remove(img) # Clean up the temporary file
        logging.info(f"Removed temporary screenshot: {img}")
    elif name == "ctrl_send":
        subprocess.run(["xdotool", "key", f"ctrl+{action['letter']}"])
        logging.info(f"Sent Ctrl+{action['letter']}")
    elif name == "type":
        subprocess.run(["xdotool", "type", action['text']])
        logging.info(f"Typed text: '{action['text']}'")
    elif name == "scroll_down":
        times = action.get('times', 0)
        if times > 0:
            win_id = subprocess.check_output(["xdotool", "getactivewindow"]).decode().strip()
            subprocess.run(["xdotool", "windowactivate", win_id])
            time.sleep(0.3)
            subprocess.run(["xdotool", "mousemove", "--window", win_id, "500", "300"])
            subprocess.run(["xdotool", "click", "--window", win_id, "1"])
            time.sleep(0.2)
            for _ in range(times):
                subprocess.run(["xdotool", "key", "--window", win_id, "Down"])
                time.sleep(0.1)
            logging.info(f"Scrolled down {times} times.")
    elif name == "scroll_up":
        times = action.get('times', 0)
        if times > 0:
            win_id = subprocess.check_output(["xdotool", "getactivewindow"]).decode().strip()
            subprocess.run(["xdotool", "windowactivate", win_id])
            time.sleep(0.3)
            subprocess.run(["xdotool", "mousemove", "--window", win_id, "500", "300"])
            subprocess.run(["xdotool", "click", "--window", win_id, "1"])
            time.sleep(0.2)
            for _ in range(times):
                subprocess.run(["xdotool", "key", "--window", win_id, "Up"])
                time.sleep(0.1)
            logging.info(f"Scrolled up {times} times.")
    elif name == "enter":
        subprocess.run(["xdotool", "key", "Return"])
        logging.info("Sent Enter key.")
    elif name == "wait":
        time.sleep(action['seconds'])
        logging.info(f"Waited for {action['seconds']} seconds.")
    elif name == "cycle_tabs":
        title = action['title']
        logging.info(f"Cycling tabs for window title: '{title}'")
        for _ in range(10):  # Limit to 10 tries
            current_title = subprocess.check_output(["xdotool", "getwindowname", "getactivewindow"]).decode().strip()
            if title.lower() in current_title.lower():
                logging.info(f"Found window with title '{title}' after cycling.")
                break
            subprocess.run(["xdotool", "key", "ctrl+Tab"])
            time.sleep(0.5)


def find_text_coords(text: str, image_path: str):
    logging.info(f"Finding text '{text}' in image {image_path}")
    # Try pytesseract first
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(image_path)
        # Preprocess the image to improve OCR accuracy
        image = image.convert('L').point(lambda x: 0 if x < 150 else 255, '1')
        
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # For debugging, let's see what text was found
        found_words = [word for word in data["text"] if word.strip()]
        if not found_words:
            logging.warning("No text found on screen using Tesseract.")
            subprocess.run(["notify-send", "Flow OCR Debug", "No text found on screen."])
        
        for i, word in enumerate(data["text"]):
            if text.lower() in word.lower():
                # Check confidence level. Tesseract can return garbage text with low confidence.
                if int(data['conf'][i]) > 50: # Confidence threshold of 50%
                    x = data["left"][i] + data["width"][i] // 2
                    y = data["top"][i] + data["height"][i] // 2
                    logging.info(f"Found text '{text}' at coordinates ({x}, {y}) using Tesseract.")
                    return x, y
    except ImportError:
        logging.error("Pytesseract or PIL not installed. Cannot use Tesseract fallback.")
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
                logging.info(f"Found text '{text}' at coordinates ({center_x}, {center_y}) using Vision API.")
                return (center_x, center_y)
        except Exception as e:
            logging.error(f"Vision API failed: {e}")
            subprocess.run(["notify-send", "Flow OCR Debug", f"Vision API failed: {e}"])

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


def main():
    logging.info("Starting run_flow.py script.")
    flows = [f for f in FLOW_DIR.glob("*.json")]
    if not flows:
        subprocess.run(["notify-send", "Flow", "No flows found"])
        logging.warning("No flows found in flow directory.")
        return
    choice = rofi("Pick flow", [p.name for p in flows])
    if not choice:
        logging.info("No flow selected. Exiting.")
        return
    path = FLOW_DIR / choice
    try:
        with open(path) as f:
            actions = json.load(f)
        logging.info(f"Loaded flow from {path} with {len(actions)} actions.")
        for act in actions:
            run_action(act)
    except FileNotFoundError:
        logging.error(f"Flow file not found: {path}")
        subprocess.run(["notify-send", "Flow Error", f"Flow file not found: {path}"])
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from flow file {path}: {e}")
        subprocess.run(["notify-send", "Flow Error", f"Error decoding flow file: {e}"])
    except Exception as e:
        logging.critical(f"An unexpected error occurred while running flow: {e}")
        subprocess.run(["notify-send", "Flow Error", f"An unexpected error occurred: {e}"])
    logging.info("run_flow.py script finished.")


if __name__ == "__main__":
    main()
