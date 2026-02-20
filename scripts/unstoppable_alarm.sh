#!/bin/bash

STOPFILE="$HOME/alarm_stop.txt"
STOPPHRASE="My name is Abdul Hakeem bin Yasin. Adamim Yasinoglu Abdul hakeem. Ismiy Abdullah bin Yasin. I wake. I rise. It is time. I will now get up from my bed if I am on it. I swear that I will go and spray some water on my face. I am a man of the ordu. I am working to improve myself. Inshallah I will be able to fulfil my rights to my lord, myself and my family. Bismillah."
SOUND="/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"

# Set volume to 100 percent
pactl set-sink-volume @DEFAULT_SINK@ 100%

# Play once immediately
DISPLAY=:1 paplay "$SOUND"

# Loop until the stop phrase is written
while true; do
    # If stop phrase detected, exit
    if grep -Fxq "$STOPPHRASE" "$STOPFILE"; then
        rm $STOPFILE
        exit 0
    fi

    # Play sound again every 5 seconds
    DISPLAY=:1 paplay "$SOUND" &
    notify-send "In $STOPFILE"
    notify-send "Write $STOPPHRASE"
    pkill alacritty
    sleep 2
done

rm $STOPFILE
