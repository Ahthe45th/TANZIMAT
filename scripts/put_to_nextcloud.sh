#!/bin/bash

# Usage: put_to_nextcloud.sh <local_file_path> <remote_file_path>
# Example: put_to_nextcloud.sh ./BUSINESSMANAGER.xlsx Documents/BUSINESSMANAGER.xlsx

# Strict mode
set -euo pipefail

# Args check
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <local_file_path> <remote_file_path>"
    exit 1
fi

LOCAL_FILE_PATH="$1"
REMOTE_FILE_PATH="$2"

# --- Configuration (match your GET script) ---
NEXTCLOUD_USER="admin"
NEXTCLOUD_PASSWORD="R1ngYaz33dah"
NEXTCLOUD_DOMAIN="naamamuslimah.com"

WEBDAV_BASE="https://${NEXTCLOUD_DOMAIN}/remote.php/dav/files/${NEXTCLOUD_USER}"
WEBDAV_URL="${WEBDAV_BASE}/${REMOTE_FILE_PATH}"

# Ensure local file exists
if [ ! -f "$LOCAL_FILE_PATH" ]; then
    echo "Local file not found: $LOCAL_FILE_PATH"
    exit 1
fi

# --- Ensure remote directory structure exists (MKCOL on each segment) ---
REMOTE_DIR="$(dirname "$REMOTE_FILE_PATH")"
if [ "$REMOTE_DIR" != "." ]; then
    IFS='/' read -r -a PARTS <<< "$REMOTE_DIR"
    CURRENT="$WEBDAV_BASE"
    for PART in "${PARTS[@]}"; do
        [ -z "$PART" ] && continue
        CURRENT="$CURRENT/$PART"
        # MKCOL returns 201 on create, 405 if already exists — both are OK
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -u "$NEXTCLOUD_USER:$NEXTCLOUD_PASSWORD" \
            -X MKCOL "$CURRENT")
        if [[ "$HTTP_CODE" =~ ^(201|405)$ ]]; then
            : # ok
        else
            echo "Failed to ensure remote directory: $CURRENT (HTTP $HTTP_CODE)"
            exit 1
        fi
    done
fi

# --- Upload file ---
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -u "$NEXTCLOUD_USER:$NEXTCLOUD_PASSWORD" \
    -T "$LOCAL_FILE_PATH" "$WEBDAV_URL")

if [[ "$HTTP_CODE" =~ ^(200|201|204)$ ]]; then
    echo "File uploaded successfully to $REMOTE_FILE_PATH"
    exit 0
else
    echo "Error uploading the file. HTTP $HTTP_CODE"
    exit 1
fi
