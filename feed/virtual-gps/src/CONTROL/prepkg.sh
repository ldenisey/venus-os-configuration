#!/bin/bash
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Setting shell rights
chmod +x "$SCRIPT_DIR"/post*
chmod +x "$SCRIPT_DIR"/pre*
chmod +x "$SCRIPT_DIR/../opt/victronenergy/service/virtual-gps-start/run"
chmod +x "$SCRIPT_DIR/../opt/victronenergy/service/virtual-gps-start/log/run"
chmod +x "$SCRIPT_DIR/../opt/victronenergy/service/virtual-gps-udp-redirect/run"
chmod +x "$SCRIPT_DIR/../opt/victronenergy/service/virtual-gps-udp-redirect/log/run"
