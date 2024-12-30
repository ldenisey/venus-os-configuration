# Compiling and/or installing HID_MULTITOUCH driver

The *HID_MULTITOUCH* driver is needed by some touchscreen "touch" feature.
As it is not part of the default Venus OS kernel, making those touchscreens work requires installing the driver manually.

## Does my touchscreen need that ?

Hard to give an exhaustive list for sure.

Mine needs it, it is a 7" sold with the reference MPI7006, even thought it is recognized as a "QDtech MPI7003" by the Cerbo GX.
In [this post](https://forums.slimdevices.com/forum/user-forums/diy/1634975-touch-screen-problem-on-picore-bug-just-some-tslib-setting/page4#post1640389),
containing the explanation of the issue, the device in question is a MPI1001.

Common behavior is that, wherever we touch the screen, the coordinates received by the system are always the bottom right pixel.
To test it, ssh in your device :

``` bash
    opkg update
    opkg install tslib-calibrate
    ts_calibrate
```

Touch your screen in top left, top right, bottom right, bottom left corners then finally in the middle of the screen.

If the coordinates of every touch are the same, i.e. `X = 1024 Y =  600` in the following exemple, you probably need the driver :

``` console
    xres = 1024, yres = 600
    Took 1 samples...
    Top left : X = 1024 Y =  600
    Took 1 samples...
    Top right : X = 1024 Y =  600
    Took 1 samples...
    Bot right : X = 1024 Y =  600
    Took 1 samples...
    Bot left : X = 1024 Y =  600
    Took 1 samples...
    Center : X = 1024 Y =  600
    ts_calibrate: determinant is too small -- 0.000000
    Calibration failed.
```

## Compiling the driver

If you do not want to spend time on this, you can download the [already compiled driver](../drivers/hid) that matches your kernel version (to get it, ssh on your device and execute `uname -r`) and get to the next chapter.

If you want or need to compile your own driver, follow the [Kernel local compilation](./SSH-Kernel_local_compilation.md) guide and :

- at the kernel configuration step, add the line `select HID_MULTITOUCH` in the input section (below line `select HID` ~195)
of the file `/data/home/root/linux-$(uname -r)/Kconfig.venus`.
- once the compilation is over, the driver module file is available at `/data/home/root/linux-$(uname -r)/drivers/hid/hid-multitouch.ko`

## Installing the driver

SSH into your device, as root and :

- paste the driver in `/lib/modules/$(uname -r)/kernel/drivers/hid/hid-multitouch.ko`
- refresh the list of available modules with `depmod -a`

Unplug/replug the touchscreen for it to load the new driver.

> **_NOTE:_**  The driver destination is not in the `/data` folder, hence it will be overwritten by Venus OS updates. You will need to reinstall it after every firmware updates.
