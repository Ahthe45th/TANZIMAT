#!/usr/bin/env python3
"""Playback controller for Quran Polybar widget."""

import os
import json
import subprocess
import time
from pathlib import Path

STATE_DIR = os.path.expanduser("~/.config/quran_widget")
STATE_FILE = os.path.join(STATE_DIR, "state.json")
AUDIO_DIR = os.path.expanduser("~/quran/naseer_qatami")
DELAY_BETWEEN_VERSES = 0.5  # seconds


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def play_file(path: Path):
    if not path.exists():
        print(f"Missing {path}")
        return
    subprocess.run([
        "mpv",
        "--really-quiet",
        "--no-terminal",
        str(path)
    ])


def main():
    state = load_state()
    if not state:
        print("No selection found. Run quran_select.py first.")
        return

    surah = state["current_surah"]
    for ayah in range(state["start_ayah"], state["end_ayah"] + 1):
        filename = f"{int(surah):03d}{ayah:03d}.mp3"
        path = Path(AUDIO_DIR) / filename
        play_file(path)
        time.sleep(DELAY_BETWEEN_VERSES)


if __name__ == "__main__":
    main()
