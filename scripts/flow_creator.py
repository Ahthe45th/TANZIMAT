#!/usr/bin/env python3
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
FLOW_DIR = SCRIPT_DIR.parent / "flows"
FLOW_DIR.mkdir(exist_ok=True)


def rofi(prompt: str, options: List[str]) -> str:
    """Show a rofi menu and return the selected value."""
    joined = "\n".join(options)
    result = subprocess.run(
        ["rofi", "-dmenu", "-p", prompt],
        input=joined,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def rofi_input(prompt: str) -> str:
    """Prompt the user for arbitrary input using rofi."""
    return rofi(prompt, [""])


def get_mouse_coords() -> (int, int):
    """Capture the current mouse coordinates."""
    out = subprocess.check_output(["xdotool", "getmouselocation", "--shell"]).decode()
    data = dict(line.split("=") for line in out.strip().splitlines())
    return int(data["X"]), int(data["Y"])


def click_coords(x: int, y: int):
    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"])


def find_text_coords(text: str, image_path: str) -> (int, int):
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


def action_coordinate_click() -> Dict:
    subprocess.run(["notify-send", "Flow", "Move mouse and wait..."])
    time.sleep(2)
    x, y = get_mouse_coords()
    click_coords(x, y)
    return {"action": "coordinate_click", "x": x, "y": y}


def action_window_switch() -> Dict:
    desk = rofi_input("Desktop number")
    if desk:
        subprocess.run(["bspc", "desktop", "-f", f"^{desk}"])
    return {"action": "window_switch", "desktop": int(desk)}


def action_text_finder() -> Dict:
    text = rofi_input("Text to find")
    img = "/tmp/flow_screen.png"
    subprocess.run(["scrot", img])
    coords = find_text_coords(text, img)
    if coords:
        click_coords(*coords)
    else:
        subprocess.run(["notify-send", "Flow", f"Text '{text}' not found"])
    return {"action": "text_finder", "text": text}


def action_ctrl_send() -> Dict:
    letter = rofi_input("Ctrl + ?")
    if letter:
        subprocess.run(["xdotool", "key", f"ctrl+{letter}"])
    return {"action": "ctrl_send", "letter": letter}


def action_typing_action() -> Dict:
    text = rofi_input("Type text")
    subprocess.run(["xdotool", "type", text])
    return {"action": "type", "text": text}


def action_scroll_down() -> Dict:
    times = int(rofi_input("Scroll down times") or 0)
    for _ in range(times):
        subprocess.run(["xdotool", "click", "5"])
        time.sleep(0.1)
    return {"action": "scroll_down", "times": times}


def action_scroll_up() -> Dict:
    times = int(rofi_input("Scroll up times") or 0)
    for _ in range(times):
        subprocess.run(["xdotool", "click", "4"])
        time.sleep(0.1)
    return {"action": "scroll_up", "times": times}


def action_enter() -> Dict:
    subprocess.run(["xdotool", "key", "Return"])
    return {"action": "enter"}


ACTION_MAP = {
    "coordinate click": action_coordinate_click,
    "window switch": action_window_switch,
    "text finder": action_text_finder,
    "ctrl send": action_ctrl_send,
    "typing action": action_typing_action,
    "scroll down": action_scroll_down,
    "scroll up": action_scroll_up,
    "enter": action_enter,
}


def main():
    actions = []
    menu_options = list(ACTION_MAP.keys()) + ["save & exit"]

    while True:
        choice = rofi("Pick action", menu_options)
        if choice == "save & exit" or not choice:
            break
        func = ACTION_MAP.get(choice)
        if func:
            actions.append(func())

    if actions:
        name = rofi_input("Flow file name")
        if name:
            path = FLOW_DIR / f"{name}.json"
            with open(path, "w") as f:
                json.dump(actions, f, indent=2)
            subprocess.run(["notify-send", "Flow", f"Saved to {path}"])


if __name__ == "__main__":
    main()
