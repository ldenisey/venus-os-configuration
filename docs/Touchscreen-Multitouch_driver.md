# Installing the multitouch touchscreen driver

The *HID_MULTITOUCH* driver is needed by touchscreens that can handle "multitouch" feature.
As it is not part of the default Venus OS kernel, making those touchscreens work requires installing it manually.

## Does my touchscreen need that ?

Hard to give an exhaustive list. You can have a look in the [compatibility table](./Touchscreen-Configuration.md#device-compatibility) to see if your model is single touch and not.  
Else test your screen with the [calibration procedure](./Touchscreen-Configuration.md#touchscreen-calibration).

## Installation

For a quick test :
``` bash
opkg install "https://github.com/ldenisey/venus-os-configuration/raw/refs/heads/main/feed/kernel-module-hid-multitouch-$(uname -r)_$(uname -r)-r0_$(cat /etc/venus/machine).ipk"
```

Unplug/replug the screen or restart your device and test your screen. If it works, make the driver persistent to firmware upgrades by [installing mod-persist](./VenusOS-Mod_persist.md.md#how-to-install-it) then :
``` bash
persist-opkg install "kernel-module-hid-multitouch-$(uname -r)"
```

## I want to build it myself !

### Compiling the driver

If you want or need to compile your own driver, follow the [Kernel local compilation](./VenusOS-Kernel_local_compilation.md) guide and :

- at the kernel configuration step, add the line `select HID_MULTITOUCH` in the input section (below line `select HID`)
of the file `/data/home/root/linux-$(uname -r)/Kconfig.venus`.
- once the compilation is over, the driver module file is available at `/data/home/root/linux-$(uname -r)/drivers/hid/hid-multitouch.ko`

### Installing the driver

SSH into your device, as root and :

- Paste the driver in `/lib/modules/$(uname -r)/kernel/drivers/hid/hid-multitouch.ko`
- Refresh the list of available modules with `depmod -a`
- Unplug and replug your screen

> [!NOTE]  
> The driver destination is not in the `/data` folder, hence it will be overwritten by Venus OS updates. You will need to reinstall it after every firmware updates.
