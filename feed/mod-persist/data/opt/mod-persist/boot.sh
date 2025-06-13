#!/bin/sh
exec > >(multilog t s25000 n4 "/var/log/$(basename $(dirname $(realpath $0)))") 2>&1
echo "*** Starting mod-persist boot script ***"

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

echo "*** End of mod-persist boot script ***"
