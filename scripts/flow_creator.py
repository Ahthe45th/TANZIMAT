#!/usr/bin/env python3
import json
import os
import subprocess
import time
import uuid
from google.cloud import vision
import io
import glob
from pathlib import Path
from typing import Dict, List
import logging

SCRIPT_DIR = Path(__file__).resolve().parent
FLOW_DIR = SCRIPT_DIR.parent / "flows"
FLOW_DIR.mkdir(exist_ok=True)

# --- LOGGING CONFIGURATION ---
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "flow_creator.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def rofi(prompt: str, options: List[str]) -> str:
    """Show a rofi menu and return the selected value."""
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

def rofi_input(prompt: str) -> str:
    """Prompt the user for arbitrary input using rofi."""
    logging.info(f"Rofi input prompt: {prompt}")
    return rofi(prompt, [""])

def get_mouse_coords() -> (int, int):
    """Capture the current mouse coordinates."""
    try:
        out = subprocess.check_output(["xdotool", "getmouselocation", "--shell"]).decode()
        data = dict(line.split("=") for line in out.strip().splitlines())
        x, y = int(data["X"]), int(data["Y"])
        logging.info(f"Captured mouse coordinates: ({x}, {y})")
        return x, y
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting mouse coordinates: {e}")
        return 0, 0

def click_coords(x: int, y: int):
    logging.info(f"Clicking coordinates: ({x}, {y})")
    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"])

def find_text_coords(text: str, image_path: str) -> (int, int):
    logging.info(f"Finding text '{text}' in image {image_path}")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    service_account_files = glob.glob(os.path.join(script_dir, "pimpting*.json"))

    if service_account_files:
        service_account_path = service_account_files[0]
        try:
            vision_results = extract_text_with_coordinates(image_path, service_account_path)
            for result in vision_results:
                if text.lower() in result["text"].lower():
                    x = (result["x_min"] + result["x_max"]) // 2
                    y = (result["y_min"] + result["y_max"]) // 2
                    logging.info(f"Found text '{text}' at coordinates ({x}, {y}) using Vision API.")
                    return (x, y)
        except Exception as e:
            logging.warning(f"Vision API failed: {e}. Falling back to Tesseract.")
            subprocess.run(["notify-send", "Flow OCR Debug", f"Vision API failed: {e}. Falling back to Tesseract."])

    # Fallback to pytesseract
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

    logging.warning(f"Text '{text}' not found in image {image_path}.")
    return None

def extract_text_with_coordinates(image_path, service_account_path):
    """
    Extracts words and their bounding box coordinates from an image using Google Cloud Vision.
    
    Returns: list of dicts with keys: text, x_min, y_min, x_max, y_max
    """
    logging.info(f"Extracting text with coordinates from {image_path} using Vision API.")
    client = vision.ImageAnnotatorClient.from_service_account_file(service_account_path)

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if response.error.message:
        logging.error(f"Vision API error: {response.error.message}")
        raise Exception(f'API Error: {response.error.message}')

    results = []
    for annotation in response.text_annotations[1:]:  # [0] is full block
        text = annotation.description
        box = annotation.bounding_poly.vertices
        x_coords = [v.x for v in box]
        y_coords = [v.y for v in box]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        results.append({
            "text": text,
            "x_min": x_min,
            "y_min": y_min,
            "x_max": x_max,
            "y_max": y_max
        })
    logging.info(f"Extracted {len(results)} text annotations.")
    return results


def action_coordinate_click() -> Dict:
    logging.info("Action: coordinate_click")
    subprocess.run(["notify-send", "Flow", "Move mouse to target position. You have 5 seconds..."])
    time.sleep(5)
    x, y = get_mouse_coords()
    subprocess.run(["notify-send", "Flow", f"Saved coordinates: ({x}, {y})"])
    return {"action": "coordinate_click", "x": x, "y": y}


def action_window_switch() -> Dict:
    logging.info("Action: window_switch")
    desk = rofi_input("Desktop number")
    if desk:
        subprocess.run(["bspc", "desktop", "-f", f"^{desk}"])
        logging.info(f"Switched to desktop: {desk}")
    return {"action": "window_switch", "desktop": int(desk) if desk else None}


def action_text_finder() -> Dict:
    logging.info("Action: text_finder")
    text = rofi_input("Text to find")
    img = f"/tmp/flow_screen_{uuid.uuid4()}.png"
    subprocess.run(["notify-send", "Flow", "Taking screenshot for text search..."])
    subprocess.run(["scrot", img])
    coords = find_text_coords(text, img)
    if coords:
        click_coords(*coords)
        subprocess.run(["notify-send", "Flow", f"Found and clicked text: '{text}'"])
        logging.info(f"Found and clicked text: '{text}'")
    else:
        subprocess.run(["notify-send", "Flow", f"Text '{text}' not found"])
        logging.warning(f"Text '{text}' not found.")
    os.remove(img) # Clean up the temporary file
    logging.info(f"Removed temporary screenshot: {img}")
    return {"action": "text_finder", "text": text}


def action_ctrl_send() -> Dict:
    logging.info("Action: ctrl_send")
    letter = rofi_input("Ctrl + ?")
    if letter:
        subprocess.run(["xdotool", "key", f"ctrl+{letter}"])
        logging.info(f"Sent Ctrl+{letter}")
    return {"action": "ctrl_send", "letter": letter}


def action_typing_action() -> Dict:
    logging.info("Action: typing_action")
    text = rofi_input("Type text")
    subprocess.run(["xdotool", "type", text])
    logging.info(f"Typed text: '{text}'")
    return {"action": "type", "text": text}


def action_scroll_down() -> Dict:
    logging.info("Action: scroll_down")
    times = int(rofi_input("Scroll down times") or 0)
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
    return {"action": "scroll_down", "times": times}


def action_scroll_up() -> Dict:
    logging.info("Action: scroll_up")
    times = int(rofi_input("Scroll up times") or 0)
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
    return {"action": "scroll_up", "times": times}


def action_enter() -> Dict:
    logging.info("Action: enter")
    subprocess.run(["xdotool", "key", "Return"])
    logging.info("Sent Enter key.")
    return {"action": "enter"}

def action_cycle_tabs() -> Dict:
    logging.info("Action: cycle_tabs")
    title = rofi_input("Window title to find")
    logging.info(f"Cycling tabs for window title: '{title}'")
    return {"action": "cycle_tabs", "title": title}


def action_wait() -> Dict:
    logging.info("Action: wait")
    seconds = rofi_input("Seconds to wait")
    if seconds:
        time.sleep(float(seconds))
        logging.info(f"Waited for {seconds} seconds.")
        return {"action": "wait", "seconds": float(seconds)}
    return {"action": "wait", "seconds": 0}


ACTION_MAP = {
    "coordinate click": action_coordinate_click,
    "window switch": action_window_switch,
    "text finder": action_text_finder,
    "ctrl send": action_ctrl_send,
    "typing action": action_typing_action,
    "scroll down": action_scroll_down,
    "scroll up": action_scroll_up,
    "enter": action_enter,
    "wait": action_wait,
    "cycle tabs": action_cycle_tabs,
}


def main():
    logging.info("Starting flow_creator.py script.")
    actions = []
    menu_options = list(ACTION_MAP.keys()) + ["save & exit", "quit"]

    while True:
        choice = rofi("Pick action", menu_options)
        if choice == "save & exit" or not choice:
            logging.info("Exiting flow creation loop.")
            break
        if choice == "quit":
            logging.info("Quitting flow_creator.py script.")
            return
        func = ACTION_MAP.get(choice)
        if func:
            try:
                actions.append(func())
            except Exception as e:
                logging.error(f"Error executing action {choice}: {e}")
                subprocess.run(["notify-send", "Flow Error", f"Error executing action {choice}: {e}"])

    if actions:
        name = rofi_input("Flow file name")
        if name:
            path = FLOW_DIR / f"{name}.json"
            try:
                with open(path, "w") as f:
                    json.dump(actions, f, indent=2)
                subprocess.run(["notify-send", "Flow", f"Saved to {path}"])
                logging.info(f"Flow saved to {path}")
            except Exception as e:
                logging.error(f"Error saving flow to {path}: {e}")
                subprocess.run(["notify-send", "Flow Error", f"Error saving flow: {e}"])


if __name__ == "__main__":
    main()
