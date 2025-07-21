#!/usr/bin/env python3

import subprocess
import time
import os
import shutil
from dotenv import load_dotenv
import logging

load_dotenv('tanzimat.env')

# --- LOGGING CONFIGURATION ---
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "adbalances.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- ENVIRONMENT SETUP FOR POLYBAR ---
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
    logging.info(f"Notification: {msg}")

def launch_firefox(profile, url):
    subprocess.Popen([FIREFOX_BIN, "-P", profile, "--no-remote", url])
    notify(f"🚀 Launched: {profile}")
    logging.info(f"Launched Firefox with profile {profile} and URL {url}")

def take_screenshot(name):
    full_path = os.path.join(SAVE_DIR, name)
    subprocess.run(["scrot", full_path])
    notify(f"📸 Screenshot: {name}")
    logging.info(f"Took screenshot: {full_path}")

def get_all_visible_window_ids():
    try:
        out = subprocess.check_output(["xdotool", "search", "--onlyvisible", "--class", "firefox"])
        logging.info("Successfully retrieved visible Firefox window IDs.")
        return out.decode().strip().splitlines()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting visible Firefox window IDs: {e}")
        return []

def focus_window(win_id):
    subprocess.run(["xdotool", "windowactivate", win_id])
    time.sleep(0.5)
    logging.info(f"Focused window ID: {win_id}")

def press_down(win_id, times=9):
    logging.info(f"Pressing Down key {times} times on window ID: {win_id}")
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
    logging.info(f"Finished pressing Down key on window ID: {win_id}")


# --- MAIN FLOW ---
logging.info("Starting adbalances.py script.")
notify("🧹 Cleaning old screenshots...")

# 0. Clean up old screenshots
if os.path.exists(SAVE_DIR):
    shutil.rmtree(SAVE_DIR)
    logging.info(f"Cleaned up old screenshots in {SAVE_DIR}")
os.makedirs(SAVE_DIR, exist_ok=True)
notify("📂 Screenshot folder reset")
logging.info(f"Created screenshot directory: {SAVE_DIR}")

# 1. Launch both Firefox windows
notify("🚀 Launching Firefox billing tabs...")
launch_firefox(PROFILE_1, URL_1)
launch_firefox(PROFILE_2, URL_2)
logging.info("Firefox billing tabs launched.")

# 2. Wait for pages to load
logging.info("Waiting for pages to load (30 seconds)...")
time.sleep(60)
logging.info("Pages loaded.")

# 3. Take full desktop screenshot (desktop 3)
take_screenshot("1_desktop3_loaded.png")
logging.info("Desktop 3 screenshot taken.")

# 4. Get visible Firefox windows
window_ids = get_all_visible_window_ids()
if len(window_ids) < 2:
    notify("❌ Less than two Firefox windows found.")
    logging.error("Less than two Firefox windows found. Exiting.")
    exit(1)
logging.info(f"Found {len(window_ids)} Firefox windows.")

# 5. Move the SECOND one to desktop 2
win_to_move = window_ids[1]
subprocess.run(["bspc", "node", win_to_move, "-d", "^2"])
notify("📤 Moved second Firefox window to desktop 2")
logging.info(f"Moved window {win_to_move} to desktop 2.")

# 6. Work with remaining window on desktop 3
win_remaining = window_ids[0]
focus_window(win_remaining)
press_down(win_remaining)
take_screenshot("2_desktop3_after_scroll.png")
logging.info("Processed remaining window on desktop 3.")

# 7. Switch to desktop 2
subprocess.run(["bspc", "desktop", "-f", "^2"])
time.sleep(1)
logging.info("Switched to desktop 2.")

# 8. Focus moved window, scroll, screenshot
focus_window(win_to_move)
press_down(win_to_move)
take_screenshot("3_desktop2_after_scroll.png")
logging.info("Processed moved window on desktop 2.")

notify("✅ All Firefox screenshots complete.")
logging.info("adbalances.py script finished successfully.")
