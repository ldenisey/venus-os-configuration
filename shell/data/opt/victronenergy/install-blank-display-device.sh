#! /bin/bash
SCRIPT_FOLDER=$(dirname "$(readlink -f "$0")")

# Preparing files in /data/ folder for firmware upgrade resilience
mkdir -p /data/opt/victronenergy/blank-display-device /data/opt/victronenergy/service/blank-display-device
cp -r "$SCRIPT_FOLDER/blank-display-device" /data/opt/victronenergy
cp -r "$SCRIPT_FOLDER/service/blank-display-device" /data/opt/victronenergy/service
chmod -R 755 /data/opt/victronenergy/blank-display-device/* /data/opt/victronenergy/service/blank-display-device/*

# Service starting commands
LN_COMMANDS=$(cat <<EOF
# Starting blank-display-device service
ln -s /data/opt/victronenergy/service/blank-display-device /service/blank-display-device
sleep 1
svc -u /service/blank-display-device
EOF
)

if [[ ! -f /data/rc.local ]]; then
    echo '#!/bin/bash' > /data/rc.local
    chmod 755 /data/rc.local
fi

if ! grep -q 'ln -s /data/opt/victronenergy/service/blank-display-device /service/blank-display-device' /data/rc.local; then
    # Save the service launch in rc.local for futur boot
    echo -e "\n$LN_COMMANDS" >> /data/rc.local
    
    # Starts the services immediately
    eval "$LN_COMMANDS"
fi
