#!/bin/bash

# Get list of WiFi SSIDs
SSID=$(nmcli -f SSID,SIGNAL dev wifi list | awk 'NR>1 && $1 != "--" {print $1}' | sort -u | rofi -dmenu -p "WiFi SSID")

# If user canceled
[ -z "$SSID" ] && exit

# Ask for password
PASSWORD=$(rofi -dmenu -password -p "Password for $SSID")

# If canceled
[ -z "$PASSWORD" ] && exit

# Connect
OUTPUT=$(nmcli dev wifi connect "$SSID" password "$PASSWORD" 2>&1)

# Notify result
notify-send "Wi-Fi Connect" "$OUTPUT"
