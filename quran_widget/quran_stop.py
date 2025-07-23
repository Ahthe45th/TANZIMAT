#!/usr/bin/env python3
"""Stops Quran playback."""

import os
import json
import socket
import time

STATE_DIR = os.path.expanduser("~/.config/quran_widget")
MPV_IPC_SOCKET = os.path.join(STATE_DIR, "mpv_socket")
PID_FILE = os.path.join(STATE_DIR, "mpv_pid")

def send_mpv_command(command):
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(MPV_IPC_SOCKET)
        sock.sendall((json.dumps(command) + '\n').encode('utf-8'))
        sock.close()
        return True
    except (socket.error, FileNotFoundError):
        return False

def main():
    if send_mpv_command({"command": ["quit"]}):
        print("Sent quit command to mpv.")
        time.sleep(0.5) # Give mpv a moment to quit
    else:
        print("No mpv instance found or IPC socket not available.")

    # Clean up PID file and socket
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    if os.path.exists(MPV_IPC_SOCKET):
        os.remove(MPV_IPC_SOCKET)
    print("Cleaned up mpv state files.")

if __name__ == "__main__":
    main()
