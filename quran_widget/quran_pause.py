#!/usr/bin/env python3
"""Pauses/unpauses Quran playback."""

import os
import json
import socket

STATE_DIR = os.path.expanduser("~/.config/quran_widget")
MPV_IPC_SOCKET = os.path.join(STATE_DIR, "mpv_socket")

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
    if send_mpv_command({"command": ["cycle", "pause"]}):
        print("Toggled mpv pause state.")
    else:
        print("No mpv instance found or IPC socket not available.")

if __name__ == "__main__":
    main()
