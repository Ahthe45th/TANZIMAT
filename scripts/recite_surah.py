#!/usr/bin/env python3

import os
import json
import random
import sys
from datetime import datetime, timedelta

# Get the absolute path of the directory containing THIS script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

import gui_utils

QURAN_DATA_FILE = os.path.join(SCRIPT_DIR, 'quran_data.json')

def check_time(input_time_str):
    try:
        now = datetime.now()
        input_time = datetime.strptime(input_time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        diff = abs(now - input_time)
        if diff > timedelta(minutes=30):
            sys.exit(1)
        gui_utils.notify("We are within the right timeframe.", "HayirzOOOOO!")
    except ValueError:
        print("Invalid time format, use HH:MM")
        sys.exit(1)

def load_quran_data():
    try:
        with open(QURAN_DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        gui_utils.notify("Recite Surah Error", f"Quran data file error: {e}")
        sys.exit(1)

def display_ayats(ayats_data, surah_name, surah_num, start_ayah, end_ayah):
    content = f"# Recitation from Surah {surah_name} ({surah_num}), Ayats {start_ayah}-{end_ayah}\n\n"
    arabic_ayats = ayats_data['arabic_ayats']
    english_ayats = ayats_data['english_ayats']

    for i in range(len(arabic_ayats)):
        content += f"**Ayah {start_ayah + i}:**\n"
        content += f"Arabic: {arabic_ayats[i]}\n"
        content += f"English: {english_ayats[i]}\n\n"

    # Use a custom zenity call for text-info with specific width/height
    try:
        import subprocess
        subprocess.run([
            "zenity", "--text-info",
            "--title=Quran Recitation",
            f"--width=800", f"--height=600"
        ], input=content.encode('utf-8'), check=True)
    except Exception:
        print(content)

def main():
    if len(sys.argv) != 2:
        print("Usage: script.py HH:MM")
        sys.exit(1)

    check_time(sys.argv[1])
    quran_data = load_quran_data()

    mode_options = ["1. Manual Recitation", "2. Recommended Recitation"]
    mode_idx = gui_utils.get_rofi_menu("Choose mode:", mode_options, index=True)
    
    if mode_idx is None:
        sys.exit(0)
    
    mode_choice = mode_idx + 1

    selected_ayats_data = {}
    surah_name = ""
    surah_num = 0
    start_ayah_display = 0
    end_ayah_display = 0

    if mode_choice == 1: # Manual Recitation
        surah_options = [f"{s['surah_number']}. {s['name']}" for s in quran_data]
        surah_idx = gui_utils.get_rofi_menu("Select Surah:", surah_options, index=True)
        if surah_idx is None: sys.exit(0)

        surah = quran_data[surah_idx]
        surah_name = surah["name"]
        surah_num = surah["surah_number"]
        num_ayats_in_surah = len(surah['arabic_ayats'])

        start_ayah_str = gui_utils.get_rofi_input(f"Enter Starting Ayah for {surah_name} (1-{num_ayats_in_surah}):")
        if not start_ayah_str: sys.exit(0)
        start_ayah = int(start_ayah_str)

        end_ayah_str = gui_utils.get_rofi_input(f"Enter Ending Ayah for {surah_name} ({start_ayah}-{num_ayats_in_surah}):")
        if not end_ayah_str: sys.exit(0)
        end_ayah = int(end_ayah_str)

        selected_ayats_data = {
            "arabic_ayats": surah["arabic_ayats"][start_ayah - 1:end_ayah],
            "english_ayats": surah["english_ayats"][start_ayah - 1:end_ayah]
        }
        start_ayah_display = start_ayah
        end_ayah_display = end_ayah

    elif mode_choice == 2: # Recommended Recitation
        num_ayats_str = gui_utils.get_rofi_input("Enter number of Ayats to recommend:")
        if not num_ayats_str: sys.exit(0)
        num_ayats_to_recommend = int(num_ayats_str)

        suitable_surahs = [s for s in quran_data if len(s["arabic_ayats"]) >= num_ayats_to_recommend and s['surah_number'] >= 25]
        if not suitable_surahs:
            gui_utils.notify("Error", "No suitable surah found.")
            sys.exit(1)

        surah = random.choice(suitable_surahs)
        surah_name = surah["name"]
        surah_num = surah["surah_number"]

        max_start_ayah_index = len(surah["arabic_ayats"]) - num_ayats_to_recommend
        start_ayah_index = random.randint(0, max_start_ayah_index)
        
        selected_ayats_data = {
            "arabic_ayats": surah["arabic_ayats"][start_ayah_index : start_ayah_index + num_ayats_to_recommend],
            "english_ayats": surah["english_ayats"][start_ayah_index : start_ayah_index + num_ayats_to_recommend]
        }
        start_ayah_display = start_ayah_index + 1
        end_ayah_display = start_ayah_index + num_ayats_to_recommend

    if selected_ayats_data:
        display_ayats(selected_ayats_data, surah_name, surah_num, start_ayah_display, end_ayah_display)
        gui_utils.notify("Recite Surah", f"Displayed ayats from Surah {surah_name} ({surah_num}).")

if __name__ == "__main__":
    main()
