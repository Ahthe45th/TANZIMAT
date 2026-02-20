#!/bin/bash

RECORDING_DIR="$HOME/Videos"
mkdir -p "$RECORDING_DIR"

# Kill any existing recordings just in case
pkill -INT ffmpeg 2>/dev/null

# Customize this line to match your resolution and source
ffmpeg \
-f x11grab -s 1920x1080 -i :0.0 \
-f pulse -i default \
-c:v libx264 -preset ultrafast -crf 23 \
-c:a aac -pix_fmt yuv420p \
"$RECORDING_DIR/recording_$(date +%Y%m%d_%H%M%S).mp4" &

echo "● REC"
