#!/bin/bash

# Get prompt from user via rofi
PROMPT=$(DISPLAY=:0 rofi -dmenu -p "Enter prompt for Codex:")

# Exit if rofi was cancelled (prompt is empty)
if [ -z "$PROMPT" ]; then
    exit 0
fi
# Run the codex command, capture its output, and parse it.
# The output is piped to grep to find the relevant lines, and then to sed to extract the message.
# 2>&1 redirects stderr to stdout to ensure all output is processed.
MESSAGE=$(/home/mehmet/.nvm/versions/node/v23.11.0/bin/codex exec --cd ~/Proyectos/TANZIMAT/NAFSIYYAH/Sandbox --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox "$PROMPT" 2>&1 | tac | awk '/\] codex/ {exit} 1' | tac)
echo $MESSAGE
# Check if a message was extracted before sending a notification.
if [ -n "$MESSAGE" ]; then
    # Set the display and send the notification.
    DISPLAY=:0 notify-send "Codex Output" "$MESSAGE"
fi
