# Touchscreen sleep

No third party touchscreen can go to sleep out of the box because **this feature has been developed specifically for Victron screens**.

Here are the various solutions depending on your situation :
- [your screen is backlight controllable](#backlight-controllable-touchscreens-fix)
- [your screen is not backlight controllable and you are using Gui V1](#gui-v1-fix)
- [your screen is not backlight controllable and you are using Gui V2](#gui-v2-workaround)

## Technical explanations

Venus OS puts official screens to sleep by turning their backlight off : the UI is still running and printed on the screen but simply can't be seen without backlight.

To do so, the Gui writes "1" or "0" to a file which is configured in */etc/venus/blank_display_device* and */etc/venus/blank_display_device.in*.  
By default those points to */sys/class/backlight/gxdisp-2-0051/bl_power* which is a sysfs file that interacts with [Victron screen specific driver](https://github.com/victronenergy/linux/blob/venus-5.10.109/drivers/video/backlight/victron-gxdisp-bl.c#L115).

For reference, in Gui V2 [this is triggered](https://github.com/victronenergy/gui-v2/blob/main/src/screenblanker.cpp#L160) by [clicking the sleep button](https://github.com/victronenergy/gui-v2/blob/main/components/StatusBar.qml#L283) or when [the timer reaches its time out](https://github.com/victronenergy/gui-v2/blob/main/src/screenblanker.cpp#L25).

If you are reading this chapter, you probably know that a [fix was found for Gui V1](#gui-v1-fix). The fix was to [redirect the "1" and "0" to the framebuffer blank file](https://communityarchive.victronenergy.com/questions/93218/generic-touchscreen-on-cerbo.html#answer-container-101953). 
Why doesn't it work for Gui V2 ?  
The Gui V1 is made with [Qt](https://www.qt.io/product/framework) version 4 whereas Gui V2 uses version 6. 
Those two Qt versions differ on how the UI is displayed on screen : Qt4 relies on a window system called [QWS](https://wiki.qt.io/Support_for_Embedded_Linux#Compact_and_Efficient_Windowing_System_QWS) whereas Qt6 uses [EGLFS](https://doc.qt.io/qt-6/embedded-linux.html#eglfs) which operates at a lower system level that takes precedence over framebuffer.

Given that EGLFS is using DRM/KMS and declares the Gui application as a DRM master, it seems there is [no possibility to make the application release KMS](https://lore.kernel.org/all/CAESbsVNtvJaPGSYqvgzGGeriH11vcnJrQ=nnCJ4sbfyE1Y1pmQ@mail.gmail.com/T/), hence no possibility to blank the screen using framebuffer or DRM without modifying Gui V2.

## Backlight controllable touchscreens fix

If you are not sure if your device is backlight controllable, easiest way is to plug it to a computer with Windows or a "full" linux OS like Ubuntu to test it.

If your screen does support backlight control, have a look in the */sys/class/backlight* folder.

If the folder is empty, you might need to compile and install its backlight driver. During [kernel compilation](VenusOS-Kernel_local_compilation.md), activate the build of the appropriate driver in *drivers/video/backlight*.

Once the backlight control is detected, you should find a folder */sys/class/backlight/\<something>*. Inside this folder, should be a file *bl_power* or similar that turns off and on the backlight when executing :

``` bash
    echo 1 > /sys/class/backlight/<something>/bl_power
    sleep 5
    echo 0 > /sys/class/backlight/<something>/bl_power
```

Once you have located the file, configure your device with :

``` bash
    echo "/sys/class/backlight/<something>/bl_power" > /etc/venus/blank_display_device
    sed -i -e "s|/sys/class/backlight/gxdisp-2-0051/bl_power|/sys/class/backlight/<something>/bl_power|g" /etc/venus/blank_display_device.in
```

> [!NOTE]  
> This configuration is not in the `/data` folder, hence it will be overwritten by Venus OS updates. You will need to redo it after every firmware updates.

> [!NOTE]  
> If you are in that case, please report your screen brand, model and the configuration file you have found with a Github PR or an issue so that I can update this page for others.


## Gui V1 fix

If your screen does not support backlight control and you are exclusively using Gui V1, you can enable sleep by running :

``` bash
    echo "/sys/class/graphics/fb0/blank" > /etc/venus/blank_display_device
    sed -i -e "s|/sys/class/backlight/gxdisp-2-0051/bl_power|/sys/class/graphics/fb0/blank|g" /etc/venus/blank_display_device.in
```

> [!NOTE]  
> This configuration is not in the `/data` folder, hence it will be overwritten by Venus OS updates. You will need to redo it after every firmware updates.

## Gui V2 workaround

### Why a workaround ?
As of now, only a degraded solution is feasible, consisting of turning off HDMI. This has two drawbacks :
- The screen turns black immediately but will keep its backlight on for a few seconds before shutting down
- Every wake up requires several seconds for the Gui V2 to load

That said, if your need is simply to turn the screen off for long period of time, during night or when you are getting out, it might be acceptable.

### Installation

To quickly test the fix :
``` bash
opkg install https://github.com/ldenisey/venus-os-configuration/raw/refs/heads/main/feed/blank-display-device_1.0.0_all.ipk
reboot
```

If it works, make it persistent to firmware upgrades by [installing mod-persist](./VenusOS-Mod_persist.md.md#how-to-install-it) then :
``` bash
persist-opkg install blank-display-device
```

### How does it work ?

File [/opt/victronenergy/blank-display-device/blank-display-device.sh](../feed/blank-display-device/opt/victronenergy/blank-display-device/blank-display-device.sh) contains the main script with the hdmi turn off/on logic.  
Folder [/opt/victronenergy/service/blank-display-device/](../feed/blank-display-device/opt/victronenergy/service/blank-display-device/) contains the service definition files that will be loaded by daemontools, the service manager of Venus OS.
