#!/bin/bash
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Setting shell rights
chmod +x "$SCRIPT_DIR"/post*
chmod +x "$SCRIPT_DIR"/pre*
chmod +x "$SCRIPT_DIR/../opt/victronenergy/blank-display-device/blank-display-device.sh"
chmod +x "$SCRIPT_DIR/../opt/victronenergy/service/blank-display-device/run"
chmod +x "$SCRIPT_DIR/../opt/victronenergy/service/blank-display-device/log/run"
