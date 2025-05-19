#!/bin/sh

# Recreate links
mkdir -p /etc/opkg-persist
ln -sf /data/etc/opkg-persist/persisted_pkgs.conf /etc/opkg-persist/persisted_pkgs.conf
ln -sf /data/etc/opkg-persist/persisted_feeds.conf /etc/opkg/persisted_feeds.conf

# Check opkg-persist installation
if ! opkg list-installed | cut -d ' ' -f 1 | grep -q "^opkg-persist$"; then
  opkg update
  opkg install opkg-persist
fi

# Check persisted packages installation
opkg-persist apply