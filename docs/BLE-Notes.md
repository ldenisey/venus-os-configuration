# Bluetooth adapter notes

## Udev configuration

### Get adapter vendor and model id

Run command `lsusb` twice, once without and once with your adapter connected to identify the newly added line.

For example, in the following :  
```console
:~# lsusb
Bus 001 Device 001: ID 1d6b:0002 Linux 6.12.23-venus-4 ehci_hcd EHCI Host Controller
Bus 001 Device 004: ID 214b:7250  USB2.0 HUB
Bus 001 Device 010: ID 0403:6001 FTDI FT232R USB UART
Bus 001 Device 013: ID 0bda:a729 Realtek Bluetooth 5.3 Radio
Bus 002 Device 001: ID 1d6b:0002 Linux 6.12.23-venus-4 ehci_hcd EHCI Host Controller
Bus 003 Device 001: ID 1d6b:0002 Linux 6.12.23-venus-4 musb-hcd MUSB HDRC host driver
Bus 003 Device 002: ID 0bda:d723 Realtek 802.11n WLAN Adapter
Bus 004 Device 001: ID 1d6b:0001 Linux 6.12.23-venus-4 ohci_hcd Generic Platform OHCI controller
Bus 005 Device 001: ID 1d6b:0001 Linux 6.12.23-venus-4 ohci_hcd Generic Platform OHCI controller
Bus 005 Device 003: ID 0484:5750 QDtech MPI7003
```
the BT controller *Realtek Bluetooth 5.3 Radio*, has vendor id *0bda* and model id *a729*.

### Get adapter dev paths

Run the following command, replacing *ID_MODEL_ID* and *ID_VENDOR_ID* values with your own :
``` bash
udevadm info --export-db | awk '/^P:/ {model=0; vendor=0; dev=""} /ID_MODEL_ID=a729/ {model=1} /ID_VENDOR_ID=0bda/ {vendor=1} /DEVPATH=/ {dev=$2} /^$/ {if(model && vendor && dev) {print dev}}' | cut -d= -f2
```

For example, it returns a path like :
```console
/devices/platform/soc/1c14000.usb/usb1/1-1/1-1.2
```

This is the path of the USB interface of your adapter.  
To get the path of its bluetooth child, run the following command, replacing *DEVPATH* with your own :
``` bash
udevadm info --export-db | awk '/^P:/ {devtype=0; subsys=0; dev=""} /DEVTYPE=host/ {devtype=1} /SUBSYSTEM=bluetooth/ {subsys=1} /DEVPATH=\/devices\/platform\/soc\/1c14000.usb\/usb1\/1-1\/1-1.2/ {dev=$2} /^$/ {if(devtype && subsys && dev) {print dev}}' | cut -d= -f2
```

For example, it returns a path like :
```console
/devices/platform/soc/1c14000.usb/usb1/1-1/1-1.2/1-1.2:1.0/bluetooth/hci1
```

### Get adapter udev info

Run, replacing dev path with your own :
``` bash
udevadm info --query=property --name=/dev/bus/usb/001/013
```

For example, it returns something like :
```console
BUSNUM=001
DEVNAME=/dev/bus/usb/001/013
DEVNUM=013
DEVPATH=/devices/platform/soc/1c14000.usb/usb1/1-1/1-1.2
DEVTYPE=usb_device
DRIVER=usb
ID_BUS=usb
ID_MODEL=Bluetooth_5.3_Radio
ID_MODEL_ENC=Bluetooth\x205.3\x20Radio
ID_MODEL_ID=a729
ID_REVISION=0200
ID_SERIAL=Realtek_Bluetooth_5.3_Radio_001122334455
ID_SERIAL_SHORT=001122334455
ID_USB_INTERFACES=:e00101:
ID_VENDOR=Realtek
ID_VENDOR_ENC=Realtek
ID_VENDOR_ID=0bda
MAJOR=189
MINOR=12
PRODUCT=bda/a729/200
SUBSYSTEM=usb
TYPE=224/1/1
USEC_INITIALIZED=166369666243
```

### Create udev rule

Common elements of the rule are :
```
ACTION=="add", SUBSYSTEM=="bluetooth", ENV{DEVTYPE}=="host", ENV{ID_SERIAL_SHORT}=="00E04C239987", RUN+="bt-config %k", SYMLINK+="hciUSB", GOTO="end"
```
- ACTION=="add" : when a new device is detected
- SUBSYSTEM=="bluetooth" : if it is a bluetooth device
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


bluetoothctl

hciconfig -a

btmgmt info

hcitool 
hcitool -i hci1 scan
hcitool -i hci1 lescan

udevadm info --export-db | grep -i -C 15 bluetooth

reapply rules : udevadm trigger && udevadm settle
sudo udevadm control --reload && sudo udevadm trigger