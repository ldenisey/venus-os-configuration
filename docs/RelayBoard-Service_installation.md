# Dbus relay board service

Relay boards allow you to add electromagnetic relays and/or MOSFET transistors to control external devices.

There are a lot of different models. Here we focus on boards with RS485, RS232 or TTL232 connectivity, as they can be plugged directly in a Venus OS device through a USB adapter.

> [!NOTE]  
> The protocol does not really matter as long as the board and the adapter share the same one.

> [!NOTE]  
> Regarding the adapter, cheap ones **should** work but you will be limited to one at a time. Expensive ones allow you to identify them individually, hence you can use several at the same time.

## Installation

``` bash
opkg install "https://github.com/ldenisey/venus-os-configuration/raw/refs/heads/main/feed/dbus-relay-board_1.0.0_all.ipk"
```

## Configuration

### Udev configuration

When plugging a USB adapter, Venus OS only detects a USB adapter, it can not know what device is behind. 

Here we will configure [udev](https://en.wikipedia.org/wiki/Udev) to identify the adapter and assign it to *dbus-relay-board* service.

#### Get adapter vendor and model id

Run command `lsusb` twice, once without and once with your adapter connected to identify the newly added line.

For example, in the following :  
```console
:~# lsusb
Bus 004 Device 006: ID 1a86:7523 QinHeng Electronics HL-340 USB-Serial adapter
Bus 004 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub
Bus 002 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 003 Device 006: ID 0403:6001 Future Technology Devices International, Ltd FT232 Serial (UART) IC
Bus 003 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 005 Device 002: ID 0bda:d723 Realtek Semiconductor Corp. 802.11n WLAN Adapter
Bus 005 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

are 2 adapters :
- *QinHeng Electronics HL-340 USB-Serial adapter*, a cheap RS485 adapter, with vendor id *1a86* and model id *7523*
- *Future Technology Devices International, Ltd FT232 Serial (UART) IC*, a better quality RS485 adapter, with vendor id *0403* and model id *6001*

#### Get adapter dev path

Run the following command, replacing *ID_MODEL_ID* and *ID_VENDOR_ID* values with your own :
``` bash
udevadm info --export-db | awk '/^P:/ {found=0; model=0; vendor=0; dev=""} /ID_MODEL_ID=6001/ {model=1} /ID_VENDOR_ID=0403/ {vendor=1} /DEVNAME=\/dev\/tty/ {dev=$2}  /^$/ {if(model && vendor && dev) {print dev}}' | cut -d= -f2
```

For example, it returns a path like :
```console
/dev/ttyUSB0
```

#### Get adapter udev info

Run, replacing dev path with your own :
``` bash
udevadm info --query=property --name=/dev/ttyUSB0
```

For example, it returns something like :
```console
DEVLINKS=/dev/serial-starter/ttyUSB0 /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 /dev/serial/by-path/platform-1c14400.usb-usb-0:1:1.0-port0 /dev/ttyUSBRelay
DEVNAME=/dev/ttyUSB0
DEVPATH=/devices/platform/soc/1c14400.usb/usb3/3-1/3-1:1.0/ttyUSB0/tty/ttyUSB0
ID_BUS=usb
ID_MODEL=USB_Serial
ID_MODEL_ENC=USB\x20Serial
ID_MODEL_FROM_DATABASE=HL-340 USB-Serial adapter
ID_MODEL_ID=7523
ID_PATH=platform-1c14400.usb-usb-0:1:1.0
ID_PATH_TAG=platform-1c14400_usb-usb-0_1_1_0
ID_REVISION=0264
ID_SERIAL=1a86_USB_Serial
ID_TYPE=generic
ID_USB_CLASS_FROM_DATABASE=Vendor Specific Class
ID_USB_DRIVER=ch341
ID_USB_INTERFACES=:ff0102:
ID_USB_INTERFACE_NUM=00
ID_VENDOR=1a86
ID_VENDOR_ENC=1a86
ID_VENDOR_FROM_DATABASE=QinHeng Electronics
ID_VENDOR_ID=1a86
MAJOR=188
MINOR=0
SUBSYSTEM=tty
USEC_INITIALIZED=221017587706
VE_SERVICE=ignore
```

#### Create udev rule

Common elements of the rule are :
```
ACTION=="add", ENV{ID_BUS}=="usb", ENV{VE_SERVICE}="relay", SYMLINK+="ttyUSBRelay", RUN+="/bin/stty -F /dev/%k -echo", GOTO="end"
```
- ACTION=="add" : when a new device is detected
- ENV{ID_BUS}=="usb" : if it is a USB device
- ENV{VE_SERVICE}="relay" : start *dbus-relay-board* to manage this device
- SYMLINK+="ttyUSBRelay" : create a static tty alias, choose another name for a second relay board
- RUN+="/bin/stty -F /dev/%k -echo" : configure device tty to disable the 'echo' feature
- GOTO="end" : if the rule is matched, ignore the others rules to prevent overriding

Specific elements are identification fields and depend of your adapter [udev info](#get-adapter-udev-info) :
- If there is a *ID_SERIAL_SHORT* field, add `ENV{ID_SERIAL_SHORT}=="your adapter ID_SERIAL_SHORT value"`
- If there is a *ID_SERIAL* field, add `ENV{ID_SERIAL}=="your adapter ID_SERIAL value"`
- Else use fields *ID_VENDOR_ID* and *ID_MODEL_ID* and add `ENV{ID_VENDOR_ID}=="your adapter ID_VENDOR_ID value", ENV{ID_MODEL_ID}=="your adapter ID_MODEL_ID value"`

Following the previous example, the entire rule would be :
```
ACTION=="add", ENV{ID_BUS}=="usb", ENV{ID_SERIAL}=="1a86_USB_Serial", ENV{VE_SERVICE}="relay", SYMLINK+="ttyUSBRelay", RUN+="/bin/stty -F /dev/%k -echo", GOTO="end"
```

Duplicate */etc/udev/rules.d/serial-starter.rules* to */etc/udev/rules.d/serial-starter.rules.ori* for precaution.  
Add the rule in file */etc/udev/rules.d/serial-starter.rules* **before** all the other *usb* rules (line ~3).  
You also need to append `LABEL="end"` to the last line of this file if not already there.

### Board configuration

Here we will describe the board so that *dbus-relay-board* service can address it correctly.

Duplicate file */etc/dbus-relay-board/template.conf* in the same folder and name it like the udev rule *SYMLINK* field, i.e. *ttyUSBRelay.conf*.

Configure *Baud*, *Parity*, *StopBits*, *Protocol* and *RelayNumber* depending of your board. You can eventually name the board and each of its relays.

### Reboot

Reboot to have the configuration loaded :
``` bash
reboot
```

## Usage

To get relay board dbus info :
``` bash
dbus -y com.victronenergy.relayboard.ttyUSBRelay / GetValue
```

To get first relay state :
``` bash
dbus -y com.victronenergy.relayboard.ttyUSBRelay /Relay/0/State GetValue
```

To set first relay state, which can be 0 or 1 :
``` bash
dbus -y com.victronenergy.relayboard.ttyUSBRelay /Relay/0/State SetValue 1
```

## Make the setup persistent to firmware upgrades

If needed, [install mod-persist](./VenusOS-Mod_persist.md.md#how-to-install-it).

To make the package persistent :
``` bash
persist-opkg install "dbus-relay-board"
```

For the udev rule, create a patch file and apply it with :
``` bash
cd /etc/udev/rules.d/
mkdir -p /data/etc/udev/rules.d/
diff serial-starter.rules.ori serial-starter.rules > /data/etc/udev/rules.d/serial-starter.rules.patch
rm serial-starter.rules
mv serial-starter.rules.ori serial-starter.rules
persist-patch install /data/etc/udev/rules.d/serial-starter.rules.patch
```

For the board configuration :
``` bash
cp /etc/dbus-relay-board/ttyUSBRelay.conf /data/etc/dbus-relay-board/ttyUSBRelay.conf
persist-file install /data/etc/dbus-relay-board/ttyUSBRelay.conf
```
