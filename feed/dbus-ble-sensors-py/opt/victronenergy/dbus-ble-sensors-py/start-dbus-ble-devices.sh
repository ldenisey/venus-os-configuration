#!/bin/sh
#
# Start script for dbus-teltonika-eye-sensor
#
# Keep this script running with daemon tools. If it exits because the
# connection crashes, or whatever, daemon tools will start a new one.
#

get_setting() {
    dbus-send --print-reply=literal --system --type=method_call \
              --dest=com.victronenergy.settings $1 \
              com.victronenergy.BusItem.GetValue |
        awk '/int32/ { print $3 }'
}

if [ -z "$(ls /sys/class/bluetooth)" ]; then
    svc -d .
    exit 1
fi

if [ "$(get_setting /Settings/Services/BleSensors)" != 1 ]; then
    svc -d .
    exit 1
fi

exec $(dirname $0)/dbus-teltonika-eye-sensor.py
