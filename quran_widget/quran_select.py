#!/usr/bin/env python3
"""Surah and Ayah range selector for Quran Polybar widget."""

import os
import json
import subprocess

STATE_DIR = os.path.expanduser("~/.config/quran_widget")
STATE_FILE = os.path.join(STATE_DIR, "state.json")

META_FILE = os.path.join(os.path.dirname(__file__), "metadata.json")

def load_env_vars(env_path):
    if not os.path.exists(env_path):
        print(f"Warning: Environment file not found at {env_path}")
        return
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

def load_metadata():
    """Load surah metadata containing number of ayat."""
    try:
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_state(surah: str, start: int, end: int):
    os.makedirs(STATE_DIR, exist_ok=True)
    data = {"current_surah": surah, "start_ayah": start, "end_ayah": end}
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def get_rofi_input(prompt: str, options: list = None) -> str:
    cmd = ["rofi", "-dmenu", "-p", prompt]
    if options:
        rofi_process = subprocess.run(cmd, input="\n".join(options), capture_output=True, text=True)
    else:
        rofi_process = subprocess.run(cmd, capture_output=True, text=True)
    return rofi_process.stdout.strip()

def main():
    env_path = "/home/mehmet/Proyectos/TANZIMAT/scripts/tanzimat.env"
    load_env_vars(env_path)

    meta = load_metadata()

    surah_options = [s for s in sorted(meta.keys(), key=int)]
    surah_selection = get_rofi_input("Select Surah (e.g., 002): ", surah_options)
    if not surah_selection:
        print("Surah selection cancelled.")
        return
    surah = surah_selection.zfill(3)

    total_ayat = int(meta.get(surah, 0))

    while True:
        start_str = get_rofi_input(f"From Ayah (1-{total_ayat}): ")
        if not start_str:
            print("Start Ayah selection cancelled.")
            return
        try:
            start = int(start_str)
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        end_str = get_rofi_input(f"To Ayah ({start}-{total_ayat}): ")
        if not end_str:
            print("End Ayah selection cancelled.")
            return
        try:
            end = int(end_str)
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        if start <= end and (total_ayat == 0 or (1 <= start <= total_ayat and 1 <= end <= total_ayat)):
            break
        print("Invalid range. Please try again.")

    save_state(surah, start, end)
    print(f"Saved range {surah}:{start}-{end}")

if __name__ == "__main__":
    main()
