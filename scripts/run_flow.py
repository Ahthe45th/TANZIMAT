#!/usr/bin/env python3
import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
FLOW_DIR = SCRIPT_DIR.parent / "flows"


def rofi(prompt: str, options: List[str]) -> str:
    joined = "\n".join(options)
    result = subprocess.run(
        ["rofi", "-dmenu", "-p", prompt],
        input=joined,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def click_coords(x: int, y: int):
    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"])


def run_action(action: Dict):
    name = action.get("action")
    if name == "coordinate_click":
        click_coords(action["x"], action["y"])
    elif name == "window_switch":
        subprocess.run(["bspc", "desktop", "-f", f"^{action['desktop']}"])
    elif name == "text_finder":
        text = action["text"]
        img = "/tmp/flow_screen.png"
        subprocess.run(["scrot", img])
        coords = find_text_coords(text, img)
        if coords:
            click_coords(*coords)
    elif name == "ctrl_send":
        subprocess.run(["xdotool", "key", f"ctrl+{action['letter']}"])
    elif name == "type":
        subprocess.run(["xdotool", "type", action['text']])
    elif name == "scroll_down":
        for _ in range(action['times']):
            subprocess.run(["xdotool", "click", "5"])
            time.sleep(0.1)
    elif name == "scroll_up":
        for _ in range(action['times']):
            subprocess.run(["xdotool", "click", "4"])
            time.sleep(0.1)
    elif name == "enter":
        subprocess.run(["xdotool", "key", "Return"])


def find_text_coords(text: str, image_path: str):
    from PIL import Image
    import pytesseract

    image = Image.open(image_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    for i, word in enumerate(data["text"]):
        if text.lower() in word.lower():
            x = data["left"][i] + data["width"][i] // 2
            y = data["top"][i] + data["height"][i] // 2
            return x, y
    return None


def main():
    flows = [f for f in FLOW_DIR.glob("*.json")]
    if not flows:
        subprocess.run(["notify-send", "Flow", "No flows found"])
        return
    choice = rofi("Pick flow", [p.name for p in flows])
    if not choice:
        return
    path = FLOW_DIR / choice
    with open(path) as f:
        actions = json.load(f)
    for act in actions:
        run_action(act)


if __name__ == "__main__":
    main()
