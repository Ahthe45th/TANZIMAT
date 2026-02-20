#!/usr/bin/env bash
set -euo pipefail

LOCAL="/home/mehmet/Proyectos/TANZIMAT"
REMOTE="nextcloud:TANZIMAT$(date)"
LOG="/home/mehmet/rclone-TANZIMAT.log"
echo $REMOTE
rclone copy "$LOCAL" "$REMOTE" \
  --checksum \
  --transfers=4 \
  --checkers=8 \
  --bwlimit=off \
  --retries=5 \
  --log-file="$LOG" --log-level=INFO
