#! /bin/bash
SCRIPT_FOLDER=$(dirname "$(readlink -f "$0")")

if ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Error: Missing port number for the UDP GPS redirect."
    echo "Usage: $0 <port>"
    exit 1
fi

# Preparing files in /data/ folder for firmware upgrade resilience
mkdir -p /data/opt/victronenergy/service/gps-udp-redirect /data/opt/victronenergy/service/gps-udp-start
cp -r "$SCRIPT_FOLDER/service/gps-udp-redirect" "$SCRIPT_FOLDER/service/gps-udp-start" /data/opt/victronenergy/service
chmod -R 755 /data/opt/victronenergy/service/gps-udp-redirect/* /data/opt/victronenergy/service/gps-udp-start/*
sed -i -e "s/udp4-recv:8500/udp4-recv:$1/g" /data/opt/victronenergy/service/gps-udp-redirect/run

# Service starting commands
LN_COMMANDS=$(cat <<EOF
# Starting gps-udp services
ln -s /data/opt/victronenergy/service/gps-udp-redirect /service/gps-udp-redirect
ln -s /data/opt/victronenergy/service/gps-udp-start /service/gps-udp-start
sleep 1
svc -u /service/gps-udp-redirect
svc -u /service/gps-udp-start
EOF
)

if [[ ! -f /data/rc.local ]]; then
    echo '#!/bin/bash' > /data/rc.local
    chmod 755 /data/rc.local
fi

if ! grep -q 'ln -s /data/opt/victronenergy/service/gps-udp-redirect /service/gps-udp-redirect' /data/rc.local; then
    # Save the services launch in rc.local for futur boot
    echo -e "\n$LN_COMMANDS" >> /data/rc.local
    
    # Starts the services immediately
    eval "$LN_COMMANDS"
fi