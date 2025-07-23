#!/usr/bin/env python3
"""Playback controller for Quran Polybar widget.

import os
import json
import subprocess
import time
from pathlib import Path
import socket # For IPC communication

STATE_DIR = os.path.expanduser("~/.config/quran_widget")
STATE_FILE = os.path.join(STATE_DIR, "state.json")
MPV_IPC_SOCKET = os.path.join(STATE_DIR, "mpv_socket") # Unique socket per user
PID_FILE = os.path.join(STATE_DIR, "mpv_pid")
PLAYLIST_FILE = os.path.join(STATE_DIR, "playlist.txt")

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

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def send_mpv_command(command):
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(MPV_IPC_SOCKET)
        sock.sendall((json.dumps(command) + '\n').encode('utf-8'))
        sock.close()
        return True
    except (socket.error, FileNotFoundError):
        return False

def kill_existing_mpv():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            pid = f.read().strip()
        if pid.isdigit():
            pid = int(pid)
            try:
                # Try to send quit command via IPC first
                if send_mpv_command({"command": ["quit"]}):
                    print(f"Sent quit command to existing mpv process {pid}")
                    time.sleep(0.5) # Give mpv a moment to quit
                
                # If still running, forcefully kill
                os.kill(pid, 9) # SIGKILL
                print(f"Killed existing mpv process {pid}")
            except OSError as e:
                print(f"Could not kill existing mpv process {pid}: {e}")
        os.remove(PID_FILE)
    if os.path.exists(MPV_IPC_SOCKET):
        os.remove(MPV_IPC_SOCKET)

def main():
    env_path = "/home/mehmet/Proyectos/TANZIMAT/scripts/tanzimat.env"
    load_env_vars(env_path)

    # Ensure state directory exists
    os.makedirs(STATE_DIR, exist_ok=True)

    # Check for existing playback and reselect if needed
    if os.path.exists(PID_FILE):
        print("Existing Quran playback detected. Stopping and reselecting...")
        kill_existing_mpv()
        # Call quran_select.py and exit
        subprocess.run(["python3", os.path.join(os.path.dirname(__file__), "quran_select.py")])
        return

    state = load_state()
    if not state:
        print("No selection found. Running quran_select.py first.")
        subprocess.run(["python3", os.path.join(os.path.dirname(__file__), "quran_select.py")])
        state = load_state() # Reload state after selection
        if not state: # If still no state after selection, exit
            print("No selection made. Exiting.")
            return

    surah = state["current_surah"]
    start_ayah = state["start_ayah"]
    end_ayah = state["end_ayah"]

    AUDIO_DIR = os.getenv("QURAN_AUDIO_DIR", os.path.expanduser("~/quran/naseer_qatami"))
    audio_path = Path(AUDIO_DIR)

    # Generate playlist
    playlist_lines = []
    for ayah in range(start_ayah, end_ayah + 1):
        filename = f"{int(surah):03d}{ayah:03d}.mp3"
        full_path = audio_path / filename
        if full_path.exists():
            playlist_lines.append(str(full_path))
        else:
            print(f"Warning: Missing audio file: {full_path}")

    if not playlist_lines:
        print("No audio files found for the selected range. Exiting.")
        return

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(playlist_lines))

    # Start mpv with playlist and IPC
    mpv_command = [
        "mpv",
        "--really-quiet",
        "--no-terminal",
        f"--input-ipc-server={MPV_IPC_SOCKET}",
        f"--playlist={PLAYLIST_FILE}"
    ]
    
    # Start mpv in a new process group to allow it to run independently
    # and be killed easily without affecting the parent shell.
    # preexec_fn=os.setsid is for creating a new process group.
    mpv_process = subprocess.Popen(mpv_command, preexec_fn=os.setsid)
    
    with open(PID_FILE, "w") as f:
        f.write(str(mpv_process.pid))
    
    print(f"Quran playback started for Surah {surah}, Ayahs {start_ayah}-{end_ayah}. PID: {mpv_process.pid}")
    print("Use quran_pause.py and quran_stop.py to control playback.")

if __name__ == "__main__":
    main()
