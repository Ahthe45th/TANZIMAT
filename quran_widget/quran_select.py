#!/usr/bin/env python3
"""Surah and Ayah range selector for Quran Polybar widget."""

import os
import json

STATE_DIR = os.path.expanduser("~/.config/quran_widget")
STATE_FILE = os.path.join(STATE_DIR, "state.json")

META_FILE = os.path.join(os.path.dirname(__file__), "metadata.json")


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


def main():
    meta = load_metadata()
    surah = input("Select Surah (e.g., 002): ").zfill(3)
    total_ayat = int(meta.get(surah, 0))

    while True:
        start = int(input("From Ayah: "))
        end = int(input("To Ayah: "))
        if start <= end and (total_ayat == 0 or end <= total_ayat):
            break
        print("Invalid range. Please try again.")

    save_state(surah, start, end)
    print(f"Saved range {surah}:{start}-{end}")


if __name__ == "__main__":
    main()
