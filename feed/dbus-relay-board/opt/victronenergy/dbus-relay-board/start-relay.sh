#!/bin/bash
#
# Start script for dbus-relay-board
#   First parameter: tty device to use
#
# Keep this script running with daemon tools. If it exits because the
# connection crashes, or whatever, daemon tools will start a new one.
#

. /opt/victronenergy/serial-starter/run-service.sh

app=/opt/victronenergy/dbus-relay-board/dbus-relay-board.py
args="--tty $tty"
start $args
