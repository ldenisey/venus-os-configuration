#!/bin/bash
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
wget -O "$SCRIPT_DIR/../opt/victronenergy/dbus-relay-board/ext/velib_python/vedbus.py" https://raw.githubusercontent.com/victronenergy/velib_python/refs/heads/master/vedbus.py
wget -O "$SCRIPT_DIR/../opt/victronenergy/dbus-relay-board/ext/velib_python/ve_utils.py" https://raw.githubusercontent.com/victronenergy/velib_python/refs/heads/master/ve_utils.py
wget -O "$SCRIPT_DIR/../opt/victronenergy/dbus-relay-board/ext/velib_python/logger.py" https://raw.githubusercontent.com/victronenergy/velib_python/refs/heads/master/logger.py
