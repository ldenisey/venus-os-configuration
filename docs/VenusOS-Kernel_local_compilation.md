# Compiling Venus OS kernel locally

## Why ?

Venus OS comes with a customized linux kernel that is optimized to the supported hardware.

If you are trying something outside its primary scope, for example connecting an unsupported device, you might be missing some driver or library.

As kernel components are specific to each unique kernel configuration, you will need to compile the kernel with the features you are missing.

This page will guide you through the kernel compilation process on your device. Do not confuse this with a "cross compilation" which consist of compiling the kernel on another machine, i.e. a computer.

> [!NOTE]  
> Those instructions have been tested on a genuine Cerbo GX device. Other devices might respond differently and require adaptations.

> [!NOTE]  
> The consequences of following those instructions are your entire responsibility. Be aware that, 
> even if the compilation itself is relatively armless, installing new kernel features can lead to unexpected behavior.
> No one, including myself and Victron team, can be held responsable.

## Prerequisites

If you are not sure about the state or your OS (because of a lot of testing, package installations, configuration modifications, ...) consider reinitialize it with a [Venus OS reset](./GuiV2-Reset_Venus_OS.md).

Knowing that compiled executable will only be compatible with the same kernel version, consider updating Venus OS to the latest version.

Configure root ssh access to the device as describe in the [Victron documentation](https://www.victronenergy.com/live/ccgx:root_access#root_access).

The process is quite long (few hours) and can slow down your device.
If you can, temporarily disable/disconnect unimportant features/devices and choose an appropriate time to do it.

## Get compilation packages and kernel sources

Connected to your device with ssh, as root :

``` bash
    # Update dependencies listing
    opkg update
    
    # Install required packages
    opkg install flex bison gcc-plugins libmpc-dev bc perl perl-modules

    # Try and install bison (https://www.gnu.org/software/bison/)
    opkg install bison

    # If it fails because it is not found in victron opkg feeds, build it manually
    wget https://ftp.gnu.org/gnu/bison/bison-3.8.tar.gz
    tar -xf bison-3.8.tar.gz
    cd bison-3.8
    ./configure
    make
    make install
    bison -h # Should show help menu
    rm -r bison-3.8 bison-3.8.tar.gz

    # Try and install flex (https://github.com/westes/flex)
    opkg install flex

    # If it fails because it is not found in victron opkg feeds, build it manually
    wget https://github.com/westes/flex/releases/download/v2.6.4/flex-2.6.4.tar.gz
    tar -xf flex-2.6.4.tar.gz
    cd flex-2.6.4
    ./configure --prefix=/usr
    make
    make install
    flex -h # Should show help menu
    rm -r flex-2.6.4 flex-2.6.4.tar.gz
    
    # Get your current kernel version (i.e. 5.10.109-venus-17). Note it, you will need it to check for futur Venus OS versions compatibity
    uname -r
    
    # Download the kernel source in root home
    cd /data/home/root
    wget https://github.com/victronenergy/linux/archive/refs/tags/v$(uname -r).tar.gz
    
    # Untar the sources
    tar -xf v$(uname -r).tar.gz
    cd linux-$(uname -r)
```

## Set default configuration

Initialize the kernel configuration with the default configuration stored in your device :

``` bash
    gzip -dkc /proc/config.gz > .config
```

## First compilation

Let's first compile the kernel without any modification from Victron default configuration.  
This ensures that the compilation environment is ok and is not wasted time : futur compilation will only compile new configuration.

The command to start the compilation is `make`. As first time compilation is long, launch the process with all the processors available and in background so that you can close your terminal and do something else in the mean time :

``` bash
    nohup make -j$(nproc) &
```

After a few hours, relaunch `make` command to check if the compilation is successful.

## Configure the kernel

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

Restart the compilation process with `make` command.

## Testing, saving and cleaning

Once the compilation is over, install and test what you have added.

You can modify the kernel configuration or sources and recompile again.

Once you are done, you should save/extract whatever files you need and the kernel configuration file for futur compilation.

Finally, to avoid any side effect of the packages and files you have installed, clean everything with :

- `rm -rf /data/home/root/linux-$(uname -r) /data/home/root/v$(uname -r).tar.gz`
- [reinstall current firmware](GuiV2-Reset_Venus_OS.md) to reconfigure and reinstall what you need from a clean base

## What to do after futur Venus OS updates ?

During Venus OS firmware updates, your device is reset : everything but the `/data` folder is wiped.
Thus, any features you have added will need to be reinstalled.

Can you reinstall the same files you have previously compiled ?
Yes, if the new Venus OS has the same kernel version (`uname -r` result) as the one you compiled them onto.
If the versions are different, recompile everything onto the new kernel version.
