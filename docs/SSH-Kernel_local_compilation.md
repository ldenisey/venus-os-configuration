# Compiling Venus OS kernel locally

## Why ?

Venus OS comes with a customized linux kernel that is optimized to the supported hardware.

If you are trying something outside its primary scope, for example connecting an unsupported device, you might be missing some driver or library.

As kernel components are specific to each unique kernel configuration, you will need to recompile the kernel as it is on your device plus the features you are missing.

This page will guide you through the kernel compilation process on your device. Do not confuse this with a "cross compilation", that would be compiling the kernel on another
machine.

> **_NOTE:_**  Those instructions have been tested on a genuine Cerbo GX device. Other devices might respond differently and require adaptations.

> **_NOTE 2:_**  The consequences of following those instructions are your entire responsibility. Be aware that, even so the compilation itself is relatively armless,
> installing new kernel features can lead to unexpected behavior from minor bugs to hardware destruction. No one, including myself and Victron team, can be held responsable.

## Prerequisites

Configure root ssh access to the device as describe in the [Victron documentation](https://www.victronenergy.com/live/ccgx:root_access#root_access).

As the result of the compilation might not be compatible with future Venus OS version, update your device to the latest firmware version.

The process is quite long (few hours) and will slow down your device.
If you can, temporarily disable/disconnect unimportant features/devices and choose an appropriate time to do it.

## Get compilation packages and kernel sources

Connected to your device with ssh, as root :

``` bash
    # Update dependencies listing
    opkg update
    
    # Install required packages
    opkg install flex bison gcc-plugins libmpc-dev bc
    
    # Get your current kernel version (i.e. 5.10.109-venus-17). Note it, you will need it to check for futur Venus OS versions compatibity
    uname -r
    
    # Download the kernel source in root home
    cd /data/home/root
    wget https://github.com/victronenergy/linux/archive/refs/tags/v$(uname -r).tar.gz
    
    # Untar the sources
    tar -xvf v$(uname -r).tar.gz
    cd linux-$(uname -r)
```

## Configure the kernel

``` bash
    # Initialize kernel configuration with the current configuration
    gzip -dkc /proc/config.gz > .config
```

Now is the time to tune the kernel configuration as you need.

There are plenty of tutos and videos explaining how to configure it.
In short, you can manually edit Kconfig/Makefile files or use the graphical interface by calling :

``` bash
    make menuconfig
```

Once your kernel customization is done, validate with :

``` bash
    make oldconfig && make prepare
```

## Compile the kernel

Here comes the long part. Start the compilation process with :

``` bash
    make
```

Note that if you loose the terminal connection the process will stop. Relaunching the same command will restart the compilation from where it stopped.

As it takes several hours, I would instead recommend to start the process in background so that you can close your terminal and go to sleep/to work/out or anything with :

``` bash
    nohup make &
```

After a few hours, relaunch `make` command to check if the compilation is successful.

## Testing, saving and cleaning

Now that you have a compiled kernel, install and test what you have added.
You can modify the kernel configuration or sources and recompile again. The compilation will be much faster as it will only recompile what you have modified.

Once you are done, you should save/extract whatever files you need. You should also save the kernel configuration file for futur compilation.

Finally, to avoid any side effect of the packages and files you have installed, clean everything with :

- `rm -rf /data/home/root/linux-$(uname -r) /data/home/root/v$(uname -r).tar.gz`
- [reinstall current firmware](GuiV2-Reset_Venus_OS.md) to reconfigure and reinstall what you need from a clean base

## What to do after futur Venus OS updates ?

During Venus OS firmware updates, your device is reset : everything but the `/data` folder is wiped.
Thus, any features you have added will need to be reinstalled.

The question is, can you reinstall the same files you have previously compiled ?
Yes, if the new Venus OS kernel has the same version (`uname -r` result) as the one you compiled them onto. If the versions are different, recompile everything onto the new kernel
version.
