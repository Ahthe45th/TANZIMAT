#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/timer.log"

exec > >(tee -a "$LOG_FILE") 2>&1

log_error() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR - $1" >> "$LOG_FILE"
  notify-send "[Timer Error]" "$1"
}

log_info() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO - $1" >> "$LOG_FILE"
}

log_info "Starting timer.sh script."

TIMERSTATE_FILE="$HOME/.config/timerstate"
TIMEMODE_FILE="$HOME/.config/.timermode"
CURRENTTIME_FILE="$HOME/.config/.currenttime"

if [ ! -f "$TIMERSTATE_FILE" ]; then
    log_error "TIMERSTATE_FILE not found: $TIMERSTATE_FILE"
    exit 1
fi

if [ "$(cat "$TIMERSTATE_FILE")" != "ON" ]; then
    log_info "Timer is OFF. Displaying current time without updating."
    jq -r .time "$CURRENTTIME_FILE" || { log_error "Failed to read time from CURRENTTIME_FILE."; exit 1; }
    exit 0
fi

if [ ! -f "$TIMEMODE_FILE" ]; then
    log_error "TIMEMODE_FILE not found: $TIMEMODE_FILE"
    exit 1
fi

if [ ! -f "$CURRENTTIME_FILE" ]; then
    log_error "CURRENTTIME_FILE not found: $CURRENTTIME_FILE"
    exit 1
fi

current_mode=$(jq -r .mode "$TIMEMODE_FILE") || { log_error "Failed to read mode from TIMEMODE_FILE."; exit 1; }
current_time=$(jq -r .time "$CURRENTTIME_FILE") || { log_error "Failed to read time from CURRENTTIME_FILE."; exit 1; }

log_info "Current mode: $current_mode, Current time: $current_time"

if [ "$current_mode" == "pomodoro" ]; then
    time_in_seconds=$(echo "$current_time" | awk -F: '{ print ($1 * 60) + $2 }')
    new_time_in_seconds=$((time_in_seconds - 1))
    if [ "$new_time_in_seconds" -lt 0 ]; then
        new_time_in_seconds=0
        notify-send "[Pomodoro]" "Time's up!"
        log_info "Pomodoro timer reached 0."
    fi
    new_minutes=$((new_time_in_seconds / 60))
    new_seconds=$((new_time_in_seconds % 60))
    printf '{"time":"%02d:%02d"}\n' "$new_minutes" "$new_seconds" > "$CURRENTTIME_FILE" || { log_error "Failed to write new time to CURRENTTIME_FILE for pomodoro."; exit 1; }
    printf ' %02d:%02d\n' "$new_minutes" "$new_seconds"
    log_info "Pomodoro time updated to %02d:%02d" "$new_minutes" "$new_seconds"
else # stopwatch
    time_in_seconds=$(echo "$current_time" | awk -F: '{ print ($1 * 60) + $2 }')
    new_time_in_seconds=$((time_in_seconds + 1))
    new_minutes=$((new_time_in_seconds / 60))
    new_seconds=$((new_time_in_seconds % 60))
    printf '{"time":"%02d:%02d"}\n' "$new_minutes" "$new_seconds" > "$CURRENTTIME_FILE" || { log_error "Failed to write new time to CURRENTTIME_FILE for stopwatch."; exit 1; }
    printf ' %02d:%02d\n' "$new_minutes" "$new_seconds"
    log_info "Stopwatch time updated to %02d:%02d" "$new_minutes" "$new_seconds"
fi

log_info "timer.sh script finished."
