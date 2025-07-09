#!/usr/bin/env python3

import subprocess
import time
import pytesseract
from PIL import Image
import requests
import os
import shutil
from dotenv import load_dotenv

load_dotenv('tanzimat.env')
# --- NOTIFY ---
def notify(message):
    subprocess.run(['notify-send', '[🟢 WhatsApp Bot]', message])

# --- FUNCTIONS ---
def get_active_window_title():
    try:
        win_id = subprocess.check_output(["xdotool", "getactivewindow"]).decode().strip()
        win_name = subprocess.check_output(["xprop", "-id", win_id, "WM_NAME"]).decode()
        return win_name
    except Exception as e:
        notify(f"❌ Failed to get window title: {e}")
        return ""

def cycle_tabs_until_whatsapp(max_tabs=10):
    for i in range(max_tabs):
        subprocess.run(["xdotool", "key", "ctrl+Tab"])
        time.sleep(1)
        title = get_active_window_title()
        if "whatsapp" in title.lower():
            notify(f"✅ Found WhatsApp tab after {i+1} switches")
            return True
    notify("❌ WhatsApp tab not found")
    return False

def click_whatsapp_or_cycle():
    notify("🔍 Trying to click WhatsApp...")
    screenshot()
    coords = find_text_coords("WhatsApp")
    if coords:
        subprocess.run(["xdotool", "mousemove", str(coords[0]), str(coords[1]), "click", "1"])
        notify("✅ Clicked WhatsApp via OCR")
    else:
        notify("⚠️ WhatsApp text not found — falling back to tab switch...")
        # Focus window by clicking screen center
        screen_x = shutil.get_terminal_size().columns * 8 // 2
        screen_y = 500  # or set dynamically
        subprocess.run(["xdotool", "mousemove", str(screen_x), str(screen_y), "click", "1"])
        time.sleep(0.5)
        cycle_tabs_until_whatsapp()

def fetch_message():
    url = "https://n8n.tuongeechat.com/webhook/73ab8574-6a42-49d4-ae71-c65138680699"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()["data"]
    except Exception as e:
        notify("❌ Failed to fetch message")
        return "MESSAGE FAILED TO LOAD"

def set_clipboard(text):
    subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'))

def screenshot(path="/tmp/screen.png"):
    subprocess.run(["scrot", path])
    return Image.open(path)

def find_text_coords(text, image_path="/tmp/screen.png"):
    image = Image.open(image_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    for i, word in enumerate(data["text"]):
        if text.lower() in word.lower():
            x = data["left"][i] + data["width"][i] // 2
            y = data["top"][i] + data["height"][i] // 2
            return (x, y)
    return None

def click_text(text):
    screenshot()
    coords = find_text_coords(text)
    if coords:
        x, y = coords
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"])
        notify(f"✅ Clicked '{text}'")
        time.sleep(0.6)
    else:
        notify(f"⚠️ Text '{text}' not found on screen.")

def paste_clipboard():
    subprocess.run(["xdotool", "key", "ctrl+shift+v"])
    time.sleep(0.2)
    subprocess.run(["xdotool", "key", "Return"])
    notify("✅ Message sent")

# --- MAIN FLOW ---

notify("🚀 Running WhatsApp bot...")

# 1. Get message
message = fetch_message()
notify("📥 Message fetched")

# 2. Set clipboard
set_clipboard(message)
notify("📋 Clipboard set")

# 3. Focus desktop 3
subprocess.run(["bspc", "desktop", "-f", "^3"])
time.sleep(1)
notify("🖥️ Switched to desktop 3")

# 4. Click WhatsApp
click_whatsapp_or_cycle()

# 5. Click BILLS
click_text("BILLS")

# 6. Paste message and send
paste_clipboard()
