# Installing the multitouch touchscreen driver

The *HID_MULTITOUCH* driver is needed by touchscreens that can handle "multitouch" feature.
As it is not part of the default Venus OS kernel, making those touchscreens work requires installing it manually.

## Does my touchscreen need that ?

Hard to give an exhaustive list. You can have a look in the [compatibility table](./Touchscreen-Configuration.md#device-compatibility) to see if your model is single touch and not.  
Else test your screen with the [calibration procedure](./Touchscreen-Configuration.md#touchscreen-calibration).

## Compiling the driver

You can skip this step by downloading an [already compiled driver](../drivers/hid) that matches your kernel version (to get it, ssh on your device and execute `uname -r`) and go to the next chapter.

If you want or need to compile your own driver, follow the [Kernel local compilation](./VenusOS-Kernel_local_compilation.md) guide and :

- at the kernel configuration step, add the line `select HID_MULTITOUCH` in the input section (below line `select HID` ~195)
of the file `/data/home/root/linux-$(uname -r)/Kconfig.venus`.
- once the compilation is over, the driver module file is available at `/data/home/root/linux-$(uname -r)/drivers/hid/hid-multitouch.ko`

## Installing the driver

SSH into your device, as root and :

- paste the driver in `/lib/modules/$(uname -r)/kernel/drivers/hid/hid-multitouch.ko`
- refresh the list of available modules with `depmod -a`

Unplug/replug the touchscreen for it to load the new driver.

> [!NOTE]  
> The driver destination is not in the `/data` folder, hence it will be overwritten by Venus OS updates. You will need to reinstall it after every firmware updates.
