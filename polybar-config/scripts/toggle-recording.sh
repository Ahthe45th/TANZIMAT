#!/bin/bash

RECORDING_DIR="$HOME/Videos"
mkdir -p "$RECORDING_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SCREEN_FILE="$RECORDING_DIR/screen_$TIMESTAMP.mp4"
CAM_FILE="$RECORDING_DIR/cam_$TIMESTAMP.mp4"
STATUS_FILE="/tmp/.screen_recording_active"

case "$1" in
    start)
        if pgrep -x ffmpeg > /dev/null; then
            notify-send "Recording already in progress."
            exit
        fi

        # Start screen recording with mic
        ffmpeg \
        -f x11grab -s 1366x768 -i :0.0 \
        -f pulse -i default \
        -c:v libx264 -preset ultrafast -crf 23 \
        -c:a aac -pix_fmt yuv420p \
        "$SCREEN_FILE" &

        SCREEN_PID=$!

        # Start webcam recording (video only)
        ffmpeg \
        -f v4l2 -s 640x480 -i /dev/video0 \
        -c:v libx264 -preset ultrafast -crf 23 \
        -movflags +faststart \
        "$CAM_FILE" &

        CAM_PID=$!

        echo "$SCREEN_PID $CAM_PID" > "$STATUS_FILE"
        notify-send "Screen Recording" "Started screen + webcam"
        ;;
    stop)
        if [ -f "$STATUS_FILE" ]; then
            read SCREEN_PID CAM_PID < "$STATUS_FILE"
            kill -INT "$SCREEN_PID" "$CAM_PID" 2>/dev/null
            rm -f "$STATUS_FILE"
            notify-send "Screen Recording" "Stopped recording"
        else
            notify-send "No recording to stop."
        fi
        ;;
    *)
        if [ -f "$STATUS_FILE" ]; then
            echo "● REC"
        else
            echo "◯ REC"
        fi
        ;;
esac
