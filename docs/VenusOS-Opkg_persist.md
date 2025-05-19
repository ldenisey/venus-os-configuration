# opkg-persist

During Venus OS firmware upgrades, everything is wiped except the */data/* folder, including packages.  
In order to avoid manual installation, you can use opkg-persist.

## How does it work

[*opkg-persist*](../feed/opkg-persist/usr/bin/opkg-persist) is a simple wrapper over [opkg](https://git.yoctoproject.org/opkg/) that allow you to persist packages and feeds in configuration files. At Venus OS boot, relink feeds and reinstall packages if an upgrade has wiped them out.

To make *opkg-persist* persistent itself, its installation package adds a call to its [boot script](../feed/opkg-persist/data/etc/opkg-persist/boot.sh) in [*/data/rc.local*](https://www.victronenergy.com/live/ccgx:root_access#hooks_to_install_run_own_code_at_boot) to check its installation and automatically reinstall itself if needed.

## How to install it

``` bash
opkg install https://github.com/ldenisey/venus-os-configuration/raw/refs/heads/main/feed/opkg-persist_1.0.0_all.ipk
```

It will :
- Install */usr/bin/opkg-persist* script
- Install configuration files in */data/etc/opkg-persist* and links them to appropriated folders in */etc*
- Append boot script execution in */data/rc.local*

## How to use it

To install packages and persist them : `opkg-persist install <pkgs>`

To remove packages and unpersist them : `opkg-persist remove <pkgs>`

To persist a feed : `opkg-persist persist-feed <name> <url>`

To unpersist a feed : `opkg-persist unpersist-feed <name>`

To get the list of persisted  feeds and packages : `opkg-persist list`

For other commands and more explanation : `opkg-persist help`