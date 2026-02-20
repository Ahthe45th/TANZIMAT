#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/git_sync.log"

exec > >(tee -a "$LOG_FILE") 2>&1

log_error() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR - $1" >> "$LOG_FILE"
  notify-send "[Git Sync Error]" "$1"
}

log_info() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO - $1" >> "$LOG_FILE"
}

log_info "Starting git_sync.sh script."

# Source the environment file
if [ -f "/home/mehmet/Proyectos/TANZIMAT/scripts/tanzimat.env" ]; then
  source "/home/mehmet/Proyectos/TANZIMAT/scripts/tanzimat.env"
  log_info "Sourced tanzimat.env"
else
  log_error "tanzimat.env not found!"
  exit 1
fi

# Navigate to the repository
cd "/home/mehmet/Proyectos/halaallove/halaallove" || { log_error "Failed to navigate to repository."; exit 1; }
log_info "Navigated to /home/mehmet/Proyectos/halaallove/halaallove"

# Perform initial git operations
git pull || { log_error "git pull failed."; exit 1; }
log_info "git pull successful."
git fetch origin || { log_error "git fetch origin failed."; exit 1; }
log_info "git fetch origin successful."

# Use rofi to select a branch
CHOSEN_BRANCH=$(echo -e "main\ndev" | rofi -dmenu -p "Select a branch to checkout")

# Exit if no branch is chosen
if [ -z "$CHOSEN_BRANCH" ]; then
  log_info "No branch selected. Exiting."
  exit 0
fi
log_info "Selected branch: $CHOSEN_BRANCH"

# Determine the other branch
if [ "$CHOSEN_BRANCH" == "main" ]; then
  OTHER_BRANCH="dev"
else
  OTHER_BRANCH="main"
fi
log_info "Other branch: $OTHER_BRANCH"

# Checkout the chosen branch and merge the other
git checkout "$CHOSEN_BRANCH" || { log_error "git checkout $CHOSEN_BRANCH failed."; exit 1; }
log_info "git checkout $CHOSEN_BRANCH successful."
git merge "$OTHER_BRANCH" || { log_error "git merge $OTHER_BRANCH failed."; exit 1; }
log_info "git merge $OTHER_BRANCH successful."

# Push the changes
git push -u origin "$CHOSEN_BRANCH" || { log_error "git push failed."; exit 1; }
log_info "Successfully synced and pushed $CHOSEN_BRANCH."
notify-send "[Git Sync]" "Successfully synced and pushed $CHOSEN_BRANCH."

