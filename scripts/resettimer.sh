#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/resettimer.log"

exec > >(tee -a "$LOG_FILE") 2>&1

log_error() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR - $1" >> "$LOG_FILE"
  notify-send "[Reset Timer Error]" "$1"
}

log_info() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO - $1" >> "$LOG_FILE"
}

log_info "Starting resettimer.sh script."

TIMEMODE_FILE="$HOME/.config/.timermode"
CURRENTTIME_FILE="$HOME/.config/.currenttime"

if [ ! -f "$TIMEMODE_FILE" ]; then
    log_error "TIMEMODE_FILE not found: $TIMEMODE_FILE"
    exit 1
fi

current_mode=$(jq -r .mode "$TIMEMODE_FILE")

if [ "$current_mode" == "pomodoro" ]; then
    echo "{\"time\":\"25:00\"}" > "$CURRENTTIME_FILE" || { log_error "Failed to write to CURRENTTIME_FILE for pomodoro mode."; exit 1; }
    log_info "Timer reset to 25:00 for pomodoro mode."
else
    echo "{\"time\":\"00:00\"}" > "$CURRENTTIME_FILE" || { log_error "Failed to write to CURRENTTIME_FILE for normal mode."; exit 1; }
    log_info "Timer reset to 00:00 for normal mode."
fi

notify-send "[Timer]" "Timer reset."
log_info "resettimer.sh script finished."

