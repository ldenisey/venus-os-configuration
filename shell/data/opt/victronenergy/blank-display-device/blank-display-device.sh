#! /bin/sh

GUI_SERVICE="/service/start-gui"
BLANK_CONFIGURATION_FILE="/etc/venus/blank_display_device"
BLANK_CONFIGURATION_ORIGINAL_VALUE="/sys/class/backlight/gxdisp-2-0051/bl_power"

# Get hdmi and input path
HDMI_BLANK_FILE_PATH="/sys/class/drm/$(ls /sys/class/drm | grep -i hdmi | head -n 1)/status"
if [[ ! -f "$HDMI_BLANK_FILE_PATH" ]]; then
    echo "Error : Can not locate HDMI status file at $HDMI_BLANK_FILE_PATH"
    svc -d .
    exit 1
fi
TOUCHSCREEN_INPUT_PATH="/dev/$(udevadm info --export-db | awk '/ID_INPUT_TOUCHSCREEN=1/{f=1; next} f && /N: input\/event/{print $2; exit}')"
if [[ ! -c "$TOUCHSCREEN_INPUT_PATH" ]]; then
    echo "Error : Can not locate touchscreen input event file at $TOUCHSCREEN_INPUT_PATH"
    svc -d .
    exit 1
fi

# Configure blank state file
BLANK_VALUE_FILE="$BLANK_CONFIGURATION_FILE.value"
echo "0" > "$BLANK_VALUE_FILE"
if [[ "$(cat $BLANK_CONFIGURATION_FILE | grep -c "$BLANK_CONFIGURATION_ORIGINAL_VALUE")" -eq 1 ]]; then
    sed -i -e "s|$BLANK_CONFIGURATION_ORIGINAL_VALUE|$BLANK_VALUE_FILE|g" "$BLANK_CONFIGURATION_FILE"
    sed -i -e "s|$BLANK_CONFIGURATION_ORIGINAL_VALUE|$BLANK_VALUE_FILE|g" "$BLANK_CONFIGURATION_FILE.in"
    svc -h $GUI_SERVICE
fi

# Monitor blank state file
while true; do
    inotifywait -q -e modify "$BLANK_VALUE_FILE"
    value=$(cat "$BLANK_VALUE_FILE")

    if [[ "$value" == "1" ]]; then
        # Turn off hdmi
        echo "Blanking screen"
        echo off > "$HDMI_BLANK_FILE_PATH"
        sleep 5

        # Wait for touchscreen event
        echo "Setting trigger for touchscreen wakeup"
        inotifywait -e access "$TOUCHSCREEN_INPUT_PATH"

        # Turn on hdmi
        echo "Touchscreen event detected, unblanking screen"
        echo on > "$HDMI_BLANK_FILE_PATH"
    else
        echo "Received other value : $value"
    fi
done
