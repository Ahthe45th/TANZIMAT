#!/bin/bash

# Alternative script for direct Chrome APK installation
# Uses apkmirror.com (trusted source) for APK download

set -euo pipefail

APK_FILE="chrome_latest.apk"

# Get latest Chrome version from apkmirror
echo "Fetching latest Chrome version..."
VERSION_PAGE=$(curl -s "https://www.apkmirror.com/apk/google-inc/chrome/" | grep -oP 'chrome-[0-9.]+-release' | head -1)

if [ -z "$VERSION_PAGE" ]; then
    echo "Failed to get Chrome version"
    exit 1
fi

# Construct download URL
DOWNLOAD_URL="https://www.apkmirror.com/wp-content/themes/APKMirror/download.php?id=$(curl -s "https://www.apkmirror.com/apk/google-inc/chrome/$VERSION_PAGE/" | grep -oP 'download.php\?id=[0-9]+"' | head -1 | cut -d'"' -f1)"

# Download APK
echo "Downloading Chrome APK from apkmirror..."
wget -O "$APK_FILE" "$DOWNLOAD_URL" || {
    echo "Download failed"
    exit 1
}

# Install via adb
echo "Installing..."
adb install "$APK_FILE" && {
    echo "✅ Chrome installed successfully"
    rm "$APK_FILE"
} || {
    echo "❌ Installation failed"
    exit 1
}