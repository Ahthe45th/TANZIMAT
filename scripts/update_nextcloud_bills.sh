#!/bin/bash

# This script fetches bill data from a webhook, updates the due dates,
# and uploads the result to a Nextcloud instance.

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo $SCRIPT_DIR
# --- Configuration ---
# WARNING: Storing passwords in plaintext is a security risk.
NC_USER="admin"
NC_PASS="R1ngYaz33dah"
NC_URL="https://naamamuslimah.com"
NC_FILE_PATH="/BILLS.md"
WEBHOOK_URL="https://n8n.tuongeechat.com/webhook/dc00ae57-d004-4f30-a9da-14fd6a632e3a"

# Construct the full WebDAV URL for the upload
WEBDAV_URL="${NC_URL}/remote.php/dav/files/${NC_USER}${NC_FILE_PATH}"

# --- Main Workflow ---
echo "Fetching, processing, and uploading bill data..."

# Use a temporary file to store the processed bill data
PROCESSED_BILLS_TMP=$(mktemp)

# 1. Fetch the raw bill data and process it with the Python script
curl -s "$WEBHOOK_URL" | /home/mehmet/miniconda3/envs/idris/bin/python "$SCRIPT_DIR/update_bills.py" > "$PROCESSED_BILLS_TMP"

# 2. Upload the processed data and capture the HTTP status code
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "${NC_USER}:${NC_PASS}" -X PUT --data-binary @"$PROCESSED_BILLS_TMP" "${WEBDAV_URL}")

# 3. Clean up the temporary file
rm "$PROCESSED_BILLS_TMP"

# Check the HTTP status code from the upload
if [[ "$HTTP_STATUS" == "204" ]] || [[ "$HTTP_STATUS" == "201" ]]; then
  echo "Upload successful! HTTP status: $HTTP_STATUS"
  notify-send "Nextcloud Sync" "✅ Bills.md was successfully updated on Nextcloud."
else
  echo "Upload failed! HTTP status: $HTTP_STATUS"
  notify-send -u critical "Nextcloud Sync" "❌ Failed to update Bills.md on Nextcloud. Status: $HTTP_STATUS"
fi
