# Debugging grid meter rs485 connection

Here are some steps to investigate your grid meter rs485 usb connection.

## Is my grid meter rs485 connection works at all ?

If you have a Carlo Gavazzi device, install and start their [configuration software](https://www.gavazzi.no/nedlasting/software/software-ucs/),
plug your rs485 usb adapter and try and connect to it.
If you see your device data, your hardware is fine.

## Is usb adapter detected ?

Plug the grid meter on your Venus device and check the log for its usb connection with `dmesg`.

The following is a valid USB connection, here with a FTDI based adapter :

``` console
    [Sat Dec 28 19:08:10 2024] usb 3-1: new full-speed USB device number 7 using ohci-platform
    [Sat Dec 28 19:08:11 2024] usb 3-1: New USB device found, idVendor=0403, idProduct=6001, bcdDevice= 6.00
    [Sat Dec 28 19:08:11 2024] usb 3-1: New USB device strings: Mfr=1, Product=2, SerialNumber=3
    [Sat Dec 28 19:08:11 2024] usb 3-1: Product: FT232R USB UART
    [Sat Dec 28 19:08:11 2024] usb 3-1: Manufacturer: FTDI
    [Sat Dec 28 19:08:11 2024] usb 3-1: SerialNumber: B000XVQ6
    [Sat Dec 28 19:08:11 2024] ftdi_sio 3-1:1.0: FTDI USB Serial Device converter detected
    [Sat Dec 28 19:08:11 2024] usb 3-1: Detected FT232RL
    [Sat Dec 28 19:08:11 2024] usb 3-1: FTDI USB Serial Device converter now attached to ttyUSB0
```

Note the *ttyUSB0* which means the device is communicating with Venus OS through */dev/ttyUSB0* terminal file.
If you have other device connected through usb, you might have *ttyUSB1*, *ttyUSB2*, ...

Error at this stage means something wrong with your USB hardware. Maybe the hardware itself is faulty, maybe there is no driver on Venus OS for it.

## Is a grid meter dbus service running ?

Execute `dbus -y | grep grid`. A response like the following means there is a running service 
reading file */dev/ttyUSB0* :

``` console
    com.victronenergy.grid.cgwacs_ttyUSB0_mb1
```

If there is no service running, try and start it manually.

## Manual trigger of the dbus service

Dbus service is started by [dbus-cgwacs](https://github.com/victronenergy/dbus-cgwacs).
Manual trigger for */dev/ttyUSB0* is done with :

``` bash
  /opt/victronenergy/dbus-cgwacs/dbus-cgwacs /dev/ttyUSB0
```

A successful execution response looks like this :

``` console
    INFO  dbus-cgwacs v2.0.23 started
    INFO  Built with Qt 6.6.3 running on 6.6.3
    INFO  Built on Nov 20 2024 at 10:27:18
    INFO  Connecting to "/dev/ttyUSB0"
    INFO  Wait for local settings on DBus...
    INFO  Local settings found
    INFO  Device ID: 103
    INFO  Device found: "008243A" @ "/dev/ttyUSB0"
    INFO  Registering service "com.victronenergy.grid.cgwacs_ttyUSB0_mb1"
    [VeQItemDbusPublisher] Registered service "com.victronenergy.grid.cgwacs_ttyUSB0_mb1"
```

Check on your local device or in VRM to see if your grid meter is shown.
In that case, your hardware is fine, you will need to dig deeper to understand why it does not start automatically.
Type *Ctrl-C* to end the previous command.

Be aware that a failing execution like the following might be self curing, meaning a second execution might be successful :

``` console
    INFO  dbus-cgwacs v2.0.23 started
    INFO  Built with Qt 6.6.3 running on 6.6.3
    INFO  Built on Nov 20 2024 at 10:27:18
    INFO  Connecting to "/dbus-cgwacs"
    INFO  Wait for local settings on DBus...
    INFO  Local settings found
    QSocketNotifier: Invalid socket specified
    QSocketNotifier: Invalid socket specified
    qt.dbus.integration: Could not disconnect "org.freedesktop.DBus" to onServiceOwnerChanged(QString,QString,QString) :
```

Once you can manually start the dbus process, reboot the Venus device to check that it starts automatically.

## Assign a custom udev rule

The grid meter is powered by 220V but the rs485 adapter is powered by USB. Thus, when not plugged to 220V, Venus OS detects the adapter but can't get any data hence can not
identify the appropriate service for it. By default, Venus OS loops forever through every possible dbus services that fails one after the other.

To avoid this looping, you can create a udev serial-starter rule that will specifically target your adapter and set dbus-cgwacs as the required service.

Depending on your adapter, you have several options to identify it in the rule. The best option is to use the serial number :

``` console
:~# udevadm info --query=property --name=/dev/ttyUSB0  | grep ID_SERIAL_SHORT
ID_SERIAL_SHORT=12345678
```

In the file `/etc/udev/rules.d/serial-starter.rules`, add the following rule, replacing the value of *ID_SERIAL_SHORT* **before** all the other *usb* rules (line ~3). In the same file, also append if needed `LABEL="end"` to the last line.

```
ACTION=="add", ENV{ID_BUS}=="usb", ENV{ID_SERIAL_SHORT}=="12345678", ENV{VE_SERVICE}="cgwacs", SYMLINK+="ttyUSBGridMeter", GOTO="end"
```

> [!NOTE]  
> The parameter *SYMLINK+="ttyUSBGridMeter"* is optional. It creates an immutable alias for this device in */dev/* folder which can be useful for scripting

> [!NOTE]  
> If your adapter does not have a *ID_SERIAL_SHORT*, replace *ENV{ID_SERIAL_SHORT}=="12345678"* by *ENV{ID_VENDOR_ID}=="1234", ENV{ID_MODEL_ID}=="1234"*, replacing with your adapter values given by `udevadm info --query=property --name=/dev/ttyUSB0`.
