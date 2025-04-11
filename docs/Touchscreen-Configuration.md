# Third party touchscreen configuration

First of all, if you are considering buying a touchscreen for you Venus OS device, you might want to read the [buying advice](#buying-advice) to avoid later configuration work.

If you already have one, here are guides for common issues :

- [Screen resolution is wrong](#screen-resolution)
- [Touches are detected but not accurate](#touchscreen-calibration)
- [Touches are not detected at all](#touchscreen-testing)
- [Screen never go to sleep](#inactive-screen-sleep)

> [!WARNING]  
> This section focuses on Victron Energy products. It might not work on Raspberry based Venus OS. Whether it does or doesn't, your feedbacks are welcome in the Github issue section for documentation updates.

## Buying advice

There are two common compatibility issues regarding third party touchscreens with Venus OS :
- The multitouch touchscreen driver is not part of Venus OS distribution. Victron screens are single touch screens and the UI does not have multitouch feature. 
- The sleep feature (screen saver) is done by turning off the screen backlight programmatically.

**In short, buy a "single touch" touchscreen with remote backlight control feature.**

As of now, here are the screens and their compatibilty status :

<a name="device-compatibility"></a>
| Screen | Single touch | Backlight | Links |
|--|--|--|--|
| QDtech MPI7006 | No | No | http://www.lcdwiki.com/7inch_HDMI_Display-H |
| QDtech MPI7003 | No | No | |
| MPI5001 | No | No | http://www.lcdwiki.com/5inch_HDMI_Display-B |
| MPI1001 | No | No | http://www.lcdwiki.com/10.1inch_HDMI_Display-H |

"Single touch = No" => [Multitouch driver installation](./Touchscreen-Multitouch_driver.md) required  
"Backlight = Yes" => [Backlight control configuration](./Touchscreen-Sleep.md#backlight-controllable-touchscreens-fix) required  
"Backlight = No" => [Gui V1 fix](./Touchscreen-Sleep.md#gui-v1-fix) or [Gui V2 workaround](./Touchscreen-Sleep.md#gui-v2-workaround) required

> [!NOTE]  
> Please help us and report your screen brand, model and eventually links and the issues you have to update the list with a Github PR or an issue.

## Screen resolution

If the Venus OS **Gui is not fullscreen or seems squished**, try and set screen resolution.
Run the following commands, replacing arguments with your screen resolution :

``` bash
    fbset -xres 1024 -yres 600
    fbset
```

You should have a confirmation like that :

``` console
    mode "1024x600-0"
        # D: 0.000 MHz, H: 0.000 kHz, V: 0.000 Hz
        geometry 1024 600 2048 2048 32
        timings 0 0 0 0 0 0 0
        accel true
        rgba 8/16,8/8,8/0,0/0
    endmode
```

## Touchscreen calibration

If your screen **does react** to touches but **not at the right place**, try and calibrate the screen.

The calibration can be done using *tslib-calibrate* package. To do so :

``` bash
    opkg update
    opkg install tslib-calibrate
    ts_calibrate
```

Touch the screen on top left, top right, bottom right and bottom left corners then in the center of the screen.  
A successful calibration looks like this :

``` console
    xres = 1024, yres = 600
    Took 11 samples...
    Top left : X =   42 Y =    0
    Took 15 samples...
    Top right : X =  996 Y =   18
    Took 17 samples...
    Bot right : X =  991 Y =  570
    Took 18 samples...
    Bot left : X =   13 Y =  576
    Took 13 samples...
    Center : X =  504 Y =  300
    16.516731 0.956169 0.029378
    43.356369 -0.005326 0.885777
    Calibration constants: 1082440 62663 1925 2841403 -349 58050 65536
```

If all the coordinates are the same and you are getting an error like in the following, as [explained in this post](https://forums.slimdevices.com/forum/user-forums/diy/1634975-touch-screen-problem-on-picore-bug-just-some-tslib-setting/page4#post1640389), you might need to [install the multitouch driver](Touchscreen-Multitouch_driver.md) :

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

## Touchscreen testing

If your touchscreen does not seem to be reactive at all, try and test it using *tslib-tests* package. To install it :

``` bash
    opkg update
    opkg install tslib-tests
    ts_test
```

Touch your screen at several places, coodinates should appear.  
If nothing appears or if the coordinates never changes, you might need to [install the multitouch driver](Touchscreen-Multitouch_driver.md).

## Inactive screen sleep

If your screen never turns off, whatever the value of *Settings* -> *Display & Language* -> *Display off time*, it is normal, no third party screen can by default :-)

Check out the [dedicated page](Touchscreen-Sleep.md) for information and fixes.
