#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <remote_file_path> <local_file_path>"
    exit 1
fi

# Assign arguments to variables
REMOTE_FILE_PATH=$1
LOCAL_FILE_PATH=$2

# --- Configuration ---
# Replace with your Nextcloud credentials and domain
# It is recommended to use an app password if you have 2FA enabled.
NEXTCLOUD_USER="admin"
NEXTCLOUD_PASSWORD="R1ngYaz33dah"
NEXTCLOUD_DOMAIN="naamamuslimah.com"

# Construct the WebDAV URL
WEBDAV_URL="https://""$NEXTCLOUD_DOMAIN""/remote.php/dav/files/""$NEXTCLOUD_USER""/""$REMOTE_FILE_PATH"

# Download the file using curl
curl -L -u "$NEXTCLOUD_USER":"$NEXTCLOUD_PASSWORD" "$WEBDAV_URL" --output "$LOCAL_FILE_PATH"

# Check if the download was successful
if [ $? -eq 0 ]; then
    echo "File downloaded successfully to $LOCAL_FILE_PATH"
else
    echo "Error downloading the file."
fi
