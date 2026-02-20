#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/kill_firefox.log"

exec > >(tee -a "$LOG_FILE") 2>&1

log_error() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR - $1" >> "$LOG_FILE"
  notify-send "[Kill Firefox Error]" "$1"
}

log_info() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO - $1" >> "$LOG_FILE"
}

log_info "Starting kill_firefox.sh script."

pkill -f firefox

if [ $? -eq 0 ]; then
  log_info "Firefox processes killed successfully."
  notify-send "[Kill Firefox]" "Firefox processes killed."
else
  log_error "Failed to kill Firefox processes or no Firefox processes were running."
fi

log_info "kill_firefox.sh script finished."
