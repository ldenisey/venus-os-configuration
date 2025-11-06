#!/bin/bash
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
mkdir -p "$SCRIPT_DIR/../opt/victronenergy/dbus-ble-devices/ext/velib_python"
wget -O "$SCRIPT_DIR/../opt/victronenergy/dbus-ble-devices/ext/velib_python/vedbus.py" https://raw.githubusercontent.com/victronenergy/velib_python/refs/heads/master/vedbus.py
wget -O "$SCRIPT_DIR/../opt/victronenergy/dbus-ble-devices/ext/velib_python/ve_utils.py" https://raw.githubusercontent.com/victronenergy/velib_python/refs/heads/master/ve_utils.py
wget -O "$SCRIPT_DIR/../opt/victronenergy/dbus-ble-devices/ext/velib_python/logger.py" https://raw.githubusercontent.com/victronenergy/velib_python/refs/heads/master/logger.py
wget -O "$SCRIPT_DIR/../opt/victronenergy/dbus-ble-devices/ext/velib_python/settingsdevice.py" https://raw.githubusercontent.com/victronenergy/velib_python/refs/heads/master/settingsdevice.py

export SKIP_CYTHON=false; pip3 install bleak --no-deps --target "$SCRIPT_DIR/../opt/victronenergy/dbus-ble-devices/ext/"
#pip3 install bleak --only-binary=:all: --target "$SCRIPT_DIR/../opt/victronenergy/dbus-ble-devices/ext/"
pip3 install gbulb --no-deps --target "$SCRIPT_DIR/../opt/victronenergy/dbus-ble-devices/ext/"
