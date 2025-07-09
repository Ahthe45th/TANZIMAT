#!/usr/bin/env python3
import os
import subprocess
import time
import base64
from openai import OpenAI
from PIL import Image
import pytesseract
import shutil 

os.remove('/tmp/_screen.png')
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
# --- ENV SETUP ---
os.environ['DISPLAY'] = ':0'
os.environ['XAUTHORITY'] = os.path.expanduser("~/.Xauthority")

client = OpenAI(api_key='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')

# --- PATHS ---
BASE_DIR = os.path.expanduser("~/firefox_shots")
IMAGES = [
    os.path.join(BASE_DIR, "2_desktop3_after_scroll.png"),
    os.path.join(BASE_DIR, "3_desktop2_after_scroll.png")
]

# --- FUNCTIONS ---
def notify(msg):
    subprocess.run(["notify-send", "[Vision→WhatsApp]", msg])

def summarize_image(path):
    notify(f"📤 Sending {os.path.basename(path)} to OpenAI")
    with open(path, "rb") as f:
        b64_img = base64.b64encode(f.read()).decode("utf-8")
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
    return response.choices[0].message.content.strip()

def set_clipboard(text):
    subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'))

def screenshot(path="/tmp/_screen.png"):
    subprocess.run(["scrot", path])
    return path

def find_text_coords(text, image_path='/tmp/_screen.png'):
    image = Image.open(image_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    for i, word in enumerate(data["text"]):
        if text.lower() in word.lower():
            x = data["left"][i] + data["width"][i] // 2
            y = data["top"][i] + data["height"][i] // 2
            return (x, y)
    return None

def click_text(text):
    img_path = screenshot()
    coords = find_text_coords(text, img_path)
    if coords:
        subprocess.run(["xdotool", "mousemove", str(coords[0]), str(coords[1]), "click", "1"])
        time.sleep(0.6)
    else:
        notify(f"❌ Couldn’t find text: {text}")

def paste_clipboard():
    subprocess.run(["xdotool", "key", "ctrl+shift+v"])
    time.sleep(0.2)
    subprocess.run(["xdotool", "key", "Return"])

# --- MAIN FLOW ---
notify("🧠 Analyzing billing screenshots...")

summaries = [summarize_image(img) for img in IMAGES]
final_message = "*BILLING REPORT*\n\n" + "\n\n---\n\n".join(summaries)
set_clipboard(final_message)
notify("📋 Billing summary copied to clipboard")

# --- SEND TO WHATSAPP ---
subprocess.run(["bspc", "desktop", "-f", "^3"])
time.sleep(1)
click_whatsapp_or_cycle()
click_text("(You)")
paste_clipboard()
notify("✅ Billing report sent via WhatsApp")
