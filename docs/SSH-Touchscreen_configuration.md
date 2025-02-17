# Touchscreen configuration

## Set screen resolution

Run the following command, replacing the screen resolution if needed :

``` bash
    fbset -xres 1024 -yres 600
```

Confirm with ```fbset``` to see it has been applied successfully.

## Calibrate

The calibration can be done using *tslib-calibrate* package. To do so :

``` bash
    opkg update
    opkg install tslib-calibrate
    ts_calibrate
```

Touch top left, top right, bottom right ten bottom left corners and finally the center of the screen.
You should get an output like :

``` console
    # ts_calibrate
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

## Timeout and sleep action blank

This configuration activates the automatic touchscreen turn-off when pressing the sleep icon and after the inactivity timeout : 

``` bash
    # Saving existing file
    cat /etc/venus/blank_display_device > /etc/venus/blank_display_device.ori
    cp /etc/venus/blank_display_device.in /etc/venus/blank_display_device.in.ori
    
    # Setting new values
    echo "/sys/class/graphics/fb0/blank" > /etc/venus/blank_display_device
    echo "/sys/class/graphics/fb0/blank % victronenergy,cerbo-gx.*" > /etc/venus/blank_display_device.in
    
    reboot
```

> **_NOTE:_**  While this configuration works well with GuiV1, it does not work with GuiV2. As of today, there is no solution to make it work with GuiV2.
