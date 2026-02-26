#!/bin/bash
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Setting shell rights
chmod +x "$SCRIPT_DIR"/post*
chmod +x "$SCRIPT_DIR"/pre*
