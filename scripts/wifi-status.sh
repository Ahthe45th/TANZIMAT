#!/bin/bash

# Get the active Wi-Fi connection name
SSID=$(nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2)

# Output result
if [ -n "$SSID" ]; then
    echo "直 $SSID"
else
    echo "直 Not connected"
fi
