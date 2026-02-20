#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/startstoptimer.log"

exec > >(tee -a "$LOG_FILE") 2>&1

log_error() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR - $1" >> "$LOG_FILE"
  notify-send "[Timer Error]" "$1"
}

log_info() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO - $1" >> "$LOG_FILE"
}

log_info "Starting startstoptimer.sh script."

TIMERSTATE_FILE="$HOME/.config/timerstate"

# Ensure the file exists
if [ ! -f "$TIMERSTATE_FILE" ]; then
    echo "OFF" > "$TIMERSTATE_FILE" || { log_error "Failed to create TIMERSTATE_FILE."; exit 1; }
    log_info "Created TIMERSTATE_FILE and set initial state to OFF."
fi

# Function to get the current state
get_state() {
    local state=$(cat "$TIMERSTATE_FILE")
    log_info "Current timer state: $state"
    echo "$state"
}

# Function to toggle the state
toggle_state() {
    current_state=$(cat "$TIMERSTATE_FILE")
    if [ "$current_state" == "ON" ]; then
        echo "OFF" > "$TIMERSTATE_FILE" || { log_error "Failed to write OFF to TIMERSTATE_FILE."; exit 1; }
        log_info "Timer state toggled to OFF."
        notify-send "[Timer]" "Timer OFF"
    else
        echo "ON" > "$TIMERSTATE_FILE" || { log_error "Failed to write ON to TIMERSTATE_FILE."; exit 1; }
        log_info "Timer state toggled to ON."
        notify-send "[Timer]" "Timer ON"
    fi
}

# Main logic
if [ "$1" == "toggle" ]; then
    toggle_state
    get_state
else
    get_state
fi

log_info "startstoptimer.sh script finished."
