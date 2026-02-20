#!/bin/bash
# Usage: ./remove_veo.sh input.mp4 output.mp4

infile="$1"
outfile="$2"

if [ -z "$infile" ] || [ -z "$outfile" ]; then
  echo "Usage: $0 input.mp4 output.mp4"
  exit 1
fi

# Watermark box size (adjust if needed)
wm_width=100
wm_height=40

# Get resolution with ffprobe
read width height < <(ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height -of csv=p=0 "$infile")

# Calculate bottom-right coords
x=$((width - wm_width))
y=$((height - wm_height))

echo "Video resolution: ${width}x${height}"
echo "Applying delogo at x=$x y=$y w=$wm_width h=$wm_height"

# Run ffmpeg
ffmpeg -i "$infile" -vf "delogo=x=$x:y=$y:w=$wm_width:h=$wm_height:show=0" -c:a copy "$outfile"
