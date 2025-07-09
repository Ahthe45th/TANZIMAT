#!/usr/bin/env python3

import subprocess
import time
import os
import shutil

# --- ENVIRONMENT SETUP FOR POLYBAR ---
os.environ['DISPLAY'] = ':0'
os.environ['XAUTHORITY'] = os.path.expanduser('~/.Xauthority')

# --- CONFIGURATION ---
FIREFOX_BIN = "firefox"
SAVE_DIR = os.path.expanduser("~/firefox_shots")

PROFILE_1 = "default-esr"
PROFILE_2 = "PH"

URL_1 = "https://business.facebook.com/billing_hub/accounts/details?asset_id=662791603221806&business_id=1590396214928706&placement=ads_manager&payment_account_id=662791603221806"
URL_2 = "https://business.facebook.com/billing_hub/accounts/details?asset_id=3943820015830789&business_id=697212649363732&placement=standalone&payment_account_id=3943820015830789"

# --- HELPERS ---
def notify(msg):
    subprocess.run(["notify-send", "[Firefox Bot]", msg])

def launch_firefox(profile, url):
    subprocess.Popen([FIREFOX_BIN, "-P", profile, "--no-remote", url])
    notify(f"🚀 Launched: {profile}")

def take_screenshot(name):
    full_path = os.path.join(SAVE_DIR, name)
    subprocess.run(["scrot", full_path])
    notify(f"📸 Screenshot: {name}")

def get_all_visible_window_ids():
    try:
        out = subprocess.check_output(["xdotool", "search", "--onlyvisible", "--class", "firefox"])
        return out.decode().strip().splitlines()
    except subprocess.CalledProcessError:
        return []

def focus_window(win_id):
    subprocess.run(["xdotool", "windowactivate", win_id])
    time.sleep(0.5)

def press_down(win_id, times=9):
    # Ensure window is active
    subprocess.run(["xdotool", "windowactivate", win_id])
    time.sleep(0.3)

    # Click in the center of the window to focus the content area
    subprocess.run(["xdotool", "mousemove", "--window", win_id, "500", "300"])
    subprocess.run(["xdotool", "click", "--window", win_id, "1"])
    time.sleep(0.2)

    # Now send Down key presses
    for _ in range(times):
        subprocess.run(["xdotool", "key", "--window", win_id, "Down"])
        time.sleep(0.1)


# --- MAIN FLOW ---
notify("🧹 Cleaning old screenshots...")

# 0. Clean up old screenshots
if os.path.exists(SAVE_DIR):
    shutil.rmtree(SAVE_DIR)
os.makedirs(SAVE_DIR, exist_ok=True)
notify("📂 Screenshot folder reset")

# 1. Launch both Firefox windows
notify("🚀 Launching Firefox billing tabs...")
launch_firefox(PROFILE_1, URL_1)
launch_firefox(PROFILE_2, URL_2)

# 2. Wait for pages to load
time.sleep(30)

# 3. Take full desktop screenshot (desktop 3)
take_screenshot("1_desktop3_loaded.png")

# 4. Get visible Firefox windows
window_ids = get_all_visible_window_ids()
if len(window_ids) < 2:
    notify("❌ Less than two Firefox windows found.")
    exit(1)

# 5. Move the SECOND one to desktop 2
win_to_move = window_ids[1]
subprocess.run(["bspc", "node", win_to_move, "-d", "^2"])
notify("📤 Moved second Firefox window to desktop 2")

# 6. Work with remaining window on desktop 3
win_remaining = window_ids[0]
focus_window(win_remaining)
press_down(win_remaining)
take_screenshot("2_desktop3_after_scroll.png")

# 7. Switch to desktop 2
subprocess.run(["bspc", "desktop", "-f", "^2"])
time.sleep(1)

# 8. Focus moved window, scroll, screenshot
focus_window(win_to_move)
press_down(win_to_move)
take_screenshot("3_desktop2_after_scroll.png")

notify("✅ All Firefox screenshots complete.")
