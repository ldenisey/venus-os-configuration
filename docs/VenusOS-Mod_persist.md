# mod-persist

During Venus OS firmware upgrades everything is wiped except the */data/* folder. Meaning any package, file or configuration you add to your Venus OS device is lost.

In order to avoid manual reinstallation at each ugrade, you can use mod-persist. As of now, it can persist opkg packages, opkg feed, files and patches.

## Installation

``` bash
opkg install https://github.com/ldenisey/venus-os-configuration/raw/refs/heads/main/feed/mod-persist_1.0.0_all.ipk
```

## Usage

### persist-opkg script

To install packages : `persist-opkg install <pkgs>`  
To remove packages : `persist-opkg remove <pkgs>`

To install a feed : `persist-opkg install-feed <name> <url>`  
To remove a feed : `persist-opkg remove-feed <name>`

To get the list of persisted feeds and packages : `persist-opkg list`

For other commands and more explanation : `persist-opkg help`

### persist-file script

To list persisted files : `persist-file list`

To install files or folders : `persist-file install <files|folders>`  
To remove files or folders : `persist-file remove <files|folders>`

*<files|folders>* are file paths located in */data* folder. They will be installed following their path, without the */data* :  
to install */etc/file*, put your new file in */data/etc/file* and execute `persist-file install /data/etc/file`.

> [!NOTE]  
> During installation, original files and folders are copied with a *.bak* extension. Those are necessary, they are used to detect if a file has been installed already and are restored by remove commands.

### persist-patch script

To list persisted patches : `persist-patch list`

To install patches : `persist-patch install <patches>`  
To remove patches : `persist-patch remove <patches>`

*<patches>* are patch file paths located in */data* folder, with a '.patch" extension. They will be executed against the file following their path, without the */data* and their extension :  
to patch file */etc/file*, put your patch file in */data/etc/file.patch* and execute `persist-patch install /data/etc/file.patch`.

> [!NOTE]  
> During installation, original files and folders are copied with a *.bak* extension. Those are necessary, they are used to detect if a file has been installed already and are restored by remove commands.



## How does it work

The modifications are stored in list files in */data/etc/mod-persist* folder. Those survive upgrades.  
During installation, *mod-persist* package adds a call to its [boot script](../feed/mod-persist/data/etc/mod-persist/boot.sh) in [*/data/rc.local*](https://www.victronenergy.com/live/ccgx:root_access#hooks_to_install_run_own_code_at_boot).
On every Venus OS start, the boot script will checks and reinstall when needed mod-persist itself and all your saved modifications.
