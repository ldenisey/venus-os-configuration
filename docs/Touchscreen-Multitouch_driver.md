# Installing the multitouch touchscreen driver

The *HID_MULTITOUCH* driver is needed by touchscreens that can handle "multitouch" feature.
As it is not part of the default Venus OS kernel, making those touchscreens work requires installing it manually.

## Does my touchscreen need that ?

Hard to give an exhaustive list. You can have a look in the [compatibility table](./Touchscreen-Configuration.md#device-compatibility) to see if your model is single touch and not.  
Else test your screen with the [calibration procedure](./Touchscreen-Configuration.md#touchscreen-calibration).

## Quick intall

For a quick and easy installation :
- [add the feed of this GitHub repository](./VenusOS-Opkg_configuration.md#adding-custom-feed)
- Log in your device
- Get your Venus OS kernel version with `uname -r`
- Install the package, replacing with your version : `opkg install kernel-module-hid-multitouch-5.10.109-venus-17`
- Unplug and replug your screen

> [!NOTE]  
> The driver destination is not in the `/data` folder, hence it will be overwritten by Venus OS updates. You will need to reinstall it after every firmware updates.

## I want to build it myself !

### Compiling the driver

If you want or need to compile your own driver, follow the [Kernel local compilation](./VenusOS-Kernel_local_compilation.md) guide and :

- at the kernel configuration step, add the line `select HID_MULTITOUCH` in the input section (below line `select HID` ~195)
of the file `/data/home/root/linux-$(uname -r)/Kconfig.venus`.
- once the compilation is over, the driver module file is available at `/data/home/root/linux-$(uname -r)/drivers/hid/hid-multitouch.ko`

### Installing the driver

SSH into your device, as root and :

- Paste the driver in `/lib/modules/$(uname -r)/kernel/drivers/hid/hid-multitouch.ko`
- Refresh the list of available modules with `depmod -a`
- Unplug and replug your screen

> [!NOTE]  
> The driver destination is not in the `/data` folder, hence it will be overwritten by Venus OS updates. You will need to reinstall it after every firmware updates.
