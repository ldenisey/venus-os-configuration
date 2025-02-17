# Stream GPS data to a Venus OS device

If you have a network device with GPS ability, instead of buying a GPS hardware,
you can stream GPS data to your Venus OS device.

## Source configuration

Here, we shall create a UDP NMEA stream to the Venus OS device. As an example, here is the configuration for a RUTX device.

In RUTX web UI, go to *Services* -> *GPS* -> *General* and enable GPS :

![](images/RUTX-GPS_conf.png)

Go to *Services* -> *GPS* -> *NMEA* -> *NMEA Forwarding* to enable and configure NMEA.
In *Host information*, set the hostname of your GX device, choose UDP protocol and set a port, i.e. 8500 :

![](images/RUTX-NMEA_conf.png)

Go to *Services* -> *GPS* -> *NMEA* -> *NMEA Sentences* and enable at least all the *GGA*, *RMC* and *GNS* sentences.

## GX device configuration

Create or append the file [`/data/rc.local`](../shell/data/rc.local) on your Venus OS device with :

``` bash
  # Configure as you wish
  UDPGPS_PORT=8500
  UDPGPS_NAME='UDP GPS'
  
  # Start background socat process to transfert data from UDP port 8500 to /dev/ttyUDPGPS device terminal file
  /usr/bin/socat UDP4-RECV:"$UDPGPS_PORT" pty,link=/dev/ttyUDPGPS,raw,nonblock,echo=0,b4800 &
  
  # Crazy background loop : relaunching gps_dbus command until it is successful
  while [ "$(pgrep gps_dbus | wc -l)" -eq 0 ]
  do
    sleep 1
    # Start a gps_dbus deamon process that reads the device terminal file fed by socat
    /opt/victronenergy/gps-dbus/gps_dbus -s /dev/ttyUDPGPS -t 0
  done &
  
  # Create background process
  (
    # Wait until the gps_dbus device is available
    while [ "$(dbus -y | grep -c ve_ttyUDPGPS)" -eq 0 ]
    do
      sleep 1
    done
  
    # Name the device created by gps_dbus process
    dbus -y com.victronenergy.gps.ve_ttyUDPGPS /ProductName SetValue "$UDPGPS_NAME" > /dev/null
  )&
   
  exit 0
```

> **_NOTE:_**  UDPGPS_PORT is the name that you will see in *Settings* -> *GPS* menu. UDPGPS_PORT is the port number you chose during source configuration. 

If needed, give execution rights to the script file with `chmod 755 /data/rc.local`.

Restart the GX device with `reboot` command.

## Debug notes

Logged in the GX device :

```console
# ps | grep -i gps | grep -v grep
 1896 root      5716 S    /usr/bin/socat UDP4-RECV:52111 pty,link=/dev/ttyUDPGPS,raw,nonblock,echo=0,b4800
 1932 root      3124 S    /opt/victronenergy/gps-dbus/gps_dbus -s /dev/ttyUDPGPS -t 0
```

Get log :
```console
# cat /var/log/gps-dbus.ttyUDPGPS/current | tai64nlocal
```

```console
# Manually send a SetValue to dbus
dbus -y com.victronenergy.gps.ve_ttyUDPGPS /ProductName SetValue "RUTX12 GPS"
# Equivalent to
dbus-send --system --dest=com.victronenergy.gps.ve_ttyUDPGPS --print-reply --type=method_call /ProductName com.victronenergy.BusItem.SetValue variant:string:"RUTX12 GPS"

# Monitoring value changes
dbus-monitor --system "destination=com.victronenergy.gps.ve_ttyUDPGPS,path=/ProductName"
(dbus-monitor --system destination=com.victronenergy.gps.ve_ttyUDPGPS,path=/ProductName &)

```
