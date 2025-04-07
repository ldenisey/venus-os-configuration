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

Go to *Services* -> *GPS* -> *NMEA* -> *NMEA Sentences* and enable at least one of *GGA*, *GNS* and *RMC* sentences, which are the three sentences parsed by Venus application.

Also make sure that the interval of forwarding is less than 5 seconds, which is the non configurable timeout that the Venus application uses to trigger a device disconnection error.

## GX device configuration

Choose one of the two possible setup.  
Quick method is great for testing your setup. Once you have found the proper configuration, robust installation is advised.

> [!NOTE]  
> Both requires [root access](https://www.victronenergy.com/live/ccgx:root_access#root_access) to your device.

### Quick setup : rc.local

Create or append the file [`/data/rc.local`](https://www.victronenergy.com/live/ccgx:root_access#hooks_to_install_run_own_code_at_boot) on your Venus OS device with :

``` bash
  # Configure as you wish
  UDPGPS_PORT=8500
  
  # Start background socat process to transfer data from UDP port 8500 to /dev/tty? device terminal file
  /usr/bin/socat UDP4-RECV:"$UDPGPS_PORT" pty,link=/dev/ttyGPS,raw,nonblock,echo=0,b4800 &
  
  # Infinite background loop to restart deamon if it fails
  while true; do
    # Start a gps_dbus daemon process that reads the device terminal file created by socat
    /opt/victronenergy/gps-dbus/gps_dbus -s /dev/ttyGPS 
    sleep 10
  done &
```

Replace the value of UDPGPS_PORT by the port number you chose during source configuration. 

If needed, give execution rights to the script file with `chmod 755 /data/rc.local`.

Restart the GX device with `reboot` command.

### Robust setup : service based

This solution is more robust as the commands will be automatically started, monitored, logged (in */var/log/* folder) and restarted when needed by daemontools, the service manager of Venus OS.

Easiest installation is to use the [dedicated script](../shell/data/opt/victronenergy/install-gps-udp.sh) with :

``` bash
  # Get and prepare sources
  wget https://github.com/ldenisey/venus-os-configuration/archive/refs/heads/main.zip 
  unzip main.zip
  chmod +x ./venus-os-configuration-main/shell/data/opt/victronenergy/install-gps-udp.sh

  # Execute installation script with your udp port
  ./venus-os-configuration-main/shell/data/opt/victronenergy/install-gps-udp.sh <your port number>

  # Clean up
  rm -r main.zip venus-os-configuration-main
```

The services should been running and configured to start at every boot. To check they are running :

``` console
  ~:# svstat /service/gps-udp-redirect
  /service/gps-udp-redirect: up (pid 2984) 759 seconds

  ~:# svstat /service/gps-udp-start
  /service/gps-udp-start: up (pid 3000) 762 seconds

  ~:# ps | grep -i gps
   2977 root      1608 S    supervise gps-udp-start
   2979 root      1608 S    supervise gps-udp-redirect
   2981 root      1752 S    multilog t s25000 n4 /var/log/gps-udp-start
   2983 root      1752 S    multilog t s25000 n4 /var/log/gps-udp-redirect
   2984 root      5716 S    /usr/bin/socat -dd udp4-recv:8500 pty,link=/dev/ttyGPS,raw,nonblock,echo=0,b4800
   3000 root      3124 S    /opt/victronenergy/gps-dbus/gps_dbus -vv -s /dev/ttyGPS
   8854 root      2692 R    grep -i gps
```

Log files can be read with :

``` bash
  cat /var/log/gps-udp-redirect/current | tai64nlocal
  cat /var/log/gps-udp-start/current | tai64nlocal
```

How does it work ?

The folder [/data/opt/victronenergy/service/gps-udp-redirect/](../shell/data/opt/victronenergy/service/gps-udp-redirect/) contains the service responsible to transfer the GPS data from UDP stream to terminal pty with a socat command.

The folder [/data/opt/victronenergy/service/gps-udp-start/](../shell/data/opt/victronenergy/service/gps-udp-start/) contains the service responsible to start [gps-dbus](https://github.com/victronenergy/dbus_gps) which is the Victron process in charge of decoding GPS data and sharing them with other process via dbus.

Those files are installed in */data/* folder so that they will survive firmware updates.  
For the services to be started at every boot, creation of symbolic links pointing to */service/* folder and services start commands are set in [*/data/rc.local*](https://www.victronenergy.com/live/ccgx:root_access#hooks_to_install_run_own_code_at_boot) file, which is automatically executed by Venus OS.
