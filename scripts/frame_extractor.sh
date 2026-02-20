#!/bin/bash

WATCH_DIR="/home/mehmet/Downloads/tobecomestillframes"
OUTPUT_DIR="/home/mehmet/Downloads/afterbecomingstillframes"

# Make sure output folder exists
mkdir -p "$OUTPUT_DIR"
mkdir -p "$WATCH_DIR"
# Watch for new files
inotifywait -m -e close_write --format "%f" "$WATCH_DIR" | while read FILE
do
    EXT="${FILE##*.}"
    BASENAME="${FILE%.*}"

    # Check if it's a video (adjust extensions as needed)
    if [[ "$EXT" =~ ^(mp4|mkv|avi|mov)$ ]]; then
        INPUT="$WATCH_DIR/$FILE"
        OUTPUT="$OUTPUT_DIR/${BASENAME}.jpg"

        # Extract first frame
        ffmpeg -i "$INPUT" -vf "select=eq(n\,0)" -q:v 3 "$OUTPUT"

        # Delete the video
        rm "$INPUT"
        echo "Processed and removed: $FILE"
    fi
done