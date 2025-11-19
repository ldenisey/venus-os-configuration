# Opkg configuration

[Opkg](https://git.yoctoproject.org/opkg/) is the package manager used in Venus OS.

Basically it :
- reads the list of feeds (repositories) set in file */etc/opkg/venus.conf* to get all the availables packages
- filters the packages that are compatible with your hardware
- gives simple commands to search, install, upgrade, remove packages

## Switching Victron feeds

Victron maintain 4 different lists of feeds, depending of your Venus OS usage :
- *release* : For most people, using "standard" Venus OS version
- *candidate* : For those using "beta" version
- *testing* : For the concerned
- *develop* : For the adventurous

To switch the feeds to another list, for example *candidate* :
``` bash
/opt/victronenergy/swupdate-scripts/set-feed.sh candidate
opkg update
```

> [!NOTE]  
> All the base feeds definition files are stored in */usr/share/venus-feed-configs/*.

## Adding custom feed

To add a custom feed, add a line with format *src/gz [feed name] [feed root url]* in either */etc/opkg/venus.conf* or a new new file in */etc/opkg* folder.  
To make opkg aware of the modification, execute `opkg update`.

For example, to add the feed of this GitHub repository :  

``` console
:~# echo "src/gz venus-os-configuration https://github.com/ldenisey/venus-os-configuration/raw/refs/heads/main/feed" > /etc/opkg/venus-os-configuration.conf
:~# opkg update
Downloading https://github.com/ldenisey/venus-os-configuration/raw/refs/heads/main/feed/Packages.gz.
Updated source 'venus-os-configuration'.
Downloading https://updates.victronenergy.com/feeds/venus/release/packages/dunfell/all/Packages.gz.
Updated source 'all'.
Downloading https://updates.victronenergy.com/feeds/venus/release/packages/dunfell/cortexa7hf-neon-vfpv4/Packages.gz.
Updated source 'cortexa7hf-neon-vfpv4'.
Downloading https://updates.victronenergy.com/feeds/venus/release/packages/dunfell/einstein/Packages.gz.
Updated source 'einstein'.
```

## Creating packages

### Prerequisistes

``` bash
opkg update
opkg install opkg-utils
cd
mkdir -p feed
```

### Package content

Create base folder :
``` bash
cd feed
mkdir -p package/CONTROL
cd package
```

Add target files with their full destination path in package/ folder and grant them appropriated rights.

Create *package/CONTROL/control* file :
``` bash
cat << EOF
Package: package
Version: 1.0.0
Maintainer: John Doe <jdoe@gmail.com>
Architecture: einstein
EOF > ./CONTROL/control
chmod 644 ./CONTROL/control
```

If needed, add preinst, postinst, prerm and/or postrm files in package/CONTROL/.

### Create package

### Automated command

``` bash
cd .. # in ./feed
opkg-build package
```

### Manual commands

To manually create the package:
``` bash
cd package
echo "2.0" > debian-binary
tar -czf control.tar.xz -C control .
tar -czf data.tar.xz -C data .
ar rv package_1.0.0_einstein.ipk control.tar.gz data.tar.gz debian-binary
```

To decompress a package : `ar x package.ipk`

### Update package feed index

``` bash
cd .. # in ./feed
opkg-make-index -p Packages .
```
