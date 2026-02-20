#!/bin/bash
# Usage: ./clean_veo_removelogo.sh input.mp4 output.mp4
# Removes a bottom-right watermark (150x60, 8px margin) using FFmpeg 'removelogo' + ImageMagick.

set -euo pipefail

in="$1"
out="$2"

if [ -z "${in:-}" ] || [ -z "${out:-}" ]; then
  echo "Usage: $0 input.mp4 output.mp4"
  exit 1
fi

# Fixed watermark size + margin
wm_w=150
wm_h=60
m=8

# 1) Get width/height and optional rotation
w="$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$in" | head -n1)"
h="$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$in" | head -n1)"
rot="$(ffprobe -v error -select_streams v:0 -show_entries stream_tags=rotate -of csv=p=0 "$in" | head -n1 || true)"
rot="${rot:-0}"

# 2) Handle rotation for display geometry
if [ "$rot" = "90" ] || [ "$rot" = "270" ]; then
  disp_w="$h"
  disp_h="$w"
else
  disp_w="$w"
  disp_h="$h"
fi

# 3) Compute mask rectangle (bottom-right, margin m)
x=$(( disp_w - wm_w - m ))
y=$(( disp_h - wm_h - m ))

if (( x < 0 || y < 0 )); then
  echo "Error: box out of frame. disp=${disp_w}x${disp_h} wm=${wm_w}x${wm_h} margin=$m"
  exit 2
fi

echo "Video: ${disp_w}x${disp_h} (rotate=${rot})"
echo "Mask rect: x=${x} y=${y} w=${wm_w} h=${wm_h}"

# 4) Build a PGM mask (white where the logo is, black elsewhere)
mask="mask_${disp_w}x${disp_h}_${x}_${y}_${wm_w}x${wm_h}.pgm"
convert -size "${disp_w}x${disp_h}" xc:black \
  -fill white -draw "rectangle ${x},${y} $((x+wm_w-1)),$((y+wm_h-1))" \
  -colorspace Gray "$mask"

# 5) Optional: preview the mask box overlay (uncomment to check)
# ffmpeg -y -i "$in" -vf "drawbox=x=${x}:y=${y}:w=${wm_w}:h=${wm_h}:color=red@0.6:t=2" -c:a copy preview.mp4

# 6) Remove the logo using the mask
ffmpeg -y -i "$in" -vf "removelogo=${mask}" -c:a copy "$out"

echo "Done -> $out"
