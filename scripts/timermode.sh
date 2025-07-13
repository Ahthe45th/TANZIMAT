#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/timermode.log"

exec > >(tee -a "$LOG_FILE") 2>&1

log_error() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR - $1" >> "$LOG_FILE"
  notify-send "[Timer Mode Error]" "$1"
}

log_info() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO - $1" >> "$LOG_FILE"
}

log_info "Starting timermode.sh script."

TIMEMODE_FILE="$HOME/.config/.timermode"

# Ensure the file exists
if [ ! -f "$TIMEMODE_FILE" ]; then
    echo "{\"mode\":\"pomodoro\"}" > "$TIMEMODE_FILE" || { log_error "Failed to create TIMEMODE_FILE."; exit 1; }
    log_info "Created TIMEMODE_FILE and set initial mode to pomodoro."
fi

# Function to get the current mode and display it
get_mode() {
    local current_mode=$(jq -r .mode "$TIMEMODE_FILE") || { log_error "Failed to read mode from TIMEMODE_FILE."; exit 1; }
    if [ "$current_mode" == "pomodoro" ]; then
        echo "Pomodoro"
        log_info "Current mode: Pomodoro"
    else
        echo "Stopwatch"
        log_info "Current mode: Stopwatch"
    fi
}

# Function to toggle the mode
toggle_mode() {
    current_mode=$(jq -r .mode "$TIMEMODE_FILE") || { log_error "Failed to read mode from TIMEMODE_FILE for toggling."; exit 1; }
    if [ "$current_mode" == "pomodoro" ]; then
        echo "{\"mode\":\"stopwatch\"}" > "$TIMEMODE_FILE" || { log_error "Failed to set mode to stopwatch."; exit 1; }
        log_info "Timer mode toggled to Stopwatch."
        notify-send "[Timer Mode]" "Switched to Stopwatch"
    else
        echo "{\"mode\":\"pomodoro\"}" > "$TIMEMODE_FILE" || { log_error "Failed to set mode to pomodoro."; exit 1; }
        log_info "Timer mode toggled to Pomodoro."
        notify-send "[Timer Mode]" "Switched to Pomodoro"
    fi
}

# Main logic
if [ "$1" == "toggle" ]; then
    toggle_mode
    get_mode
else
    get_mode
fi

log_info "timermode.sh script finished."
