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