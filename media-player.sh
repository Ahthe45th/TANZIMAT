#!/bin/bash

# Directories to search for media files
WATCHLIST_DIR="$HOME/yt-watchlist"
ENTERTAINMENT_DIR="$HOME/Downloads/Entrenimiento"

# Find all media files in the specified directories
# You can add more extensions here if needed (e.g., .avi, .mov)
MEDIA_FILES=$(find "$WATCHLIST_DIR" "$ENTERTAINMENT_DIR" -type f \( -iname "*.mp4" -o -iname "*.mkv" -o -iname "*.webm" -o -iname "*.mp3" -o -iname "*.flac" -o -iname "*.ogg" \))

# Use rofi to select a media file
SELECTED_FILE=$(echo "$MEDIA_FILES" | rofi -dmenu -p "Select Media")

# If a file was selected, play it with mpv
if [ -n "$SELECTED_FILE" ]; then
    mpv "$SELECTED_FILE"
fi
