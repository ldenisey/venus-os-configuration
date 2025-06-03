#!/bin/sh

# Expend rootfs and make it writable
/opt/victronenergy/swupdate-scripts/resize2fs.sh

# Check mod-persist installation
if ! opkg list-installed | cut -d ' ' -f 1 | grep -q "^mod-persist$"; then
  # Reinstall mod-persist
  ln -sf /data/etc/mod-persist/persisted_opkg_feeds.conf /etc/opkg/persisted_feeds.conf
  opkg update
  opkg install mod-persist
fi

# Check persisted packages installation
persist-opkg apply

# Check persisted files installation
persist-file apply

# Check persisted files installation
persist-patch apply
