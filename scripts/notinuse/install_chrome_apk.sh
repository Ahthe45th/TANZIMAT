#!/bin/bash

# Script to download and install Chrome APK on Android device
# Requires: adb (Android Debug Bridge) installed and device connected

set -euo pipefail

APK_FILE="chrome_latest.apk"

# Alternative APK sources (use with caution)
APK_URLS=(
    "https://apk-dl.com/google-chrome-fast-secure"
    "https://apkpure.com/chrome-fast-secure/com.android.chrome/download"
)

# Try multiple sources
echo "Attempting to download Chrome APK..."
for url in "${APK_URLS[@]}"; do
    echo "Trying: $url"
    if wget -O "$APK_FILE" "$url" 2>/dev/null && [ -s "$APK_FILE" ]; then
        echo "Download successful"
        break
    fi
    echo "Failed, trying next source..."
done

# Check if download succeeded
if [ ! -s "$APK_FILE" ]; then
    echo "All download attempts failed"
    echo "Alternative: Install via Google Play Store using adb"
    echo "Run: adb shell am start -a android.intent.action.VIEW -d 'market://details?id=com.android.chrome'"
    exit 1
fi

# Check if adb is available
if ! command -v adb &> /dev/null; then
    echo "ADB not found. Please install Android Platform Tools"
    exit 1
fi

# Check device connection
echo "Checking device connection..."
if ! adb devices | grep -v "List of devices" | grep -q "device"; then
    echo "No Android device connected or unauthorized"
    echo "Enable USB debugging and authorize this computer"
    exit 1
fi

# Install APK
echo "Installing Chrome..."
adb install "$APK_FILE"

if [ $? -eq 0 ]; then
    echo "Chrome installed successfully"
    rm "$APK_FILE"
else
    echo "Installation failed"
    exit 1
fi