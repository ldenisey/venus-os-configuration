# Configuring SSL certificates

* [Adding root CA](#adding-root-ca)
* [Replacing Victron SSL default certificate](#replacing-victron-ssl-default-certificate)

## Adding root CAs

Append your root CA to `/etc/ssl/certs/ca-certificates.crt`.

## Replacing Victron SSL default certificate

### Copy your certificate

Copy your certificate and its private key to `/data/etc/ssl`, grant them appropriated rights :

``` bash
    chmod 644 /data/etc/ssl/your-cert.pem
    chmod 400 /data/etc/ssl/your-cert-key.pem
```

### Configure your certificate

Here are the configuration files that uses certificates :

| Tool     | File                                  | Default certificates                                         |
| -------- | ------------------------------------- | ------------------------------------------------------------ |
| Gui      | /etc/nginx/sites-available/https.site | /data/etc/ssl/venus.local.key, /data/etc/ssl/venus.local.crt |
| Node-RED | /etc/nginx/sites-available/node-red   | /data/etc/ssl/venus.local.key, /data/etc/ssl/venus.local.crt |
| FlashMQ  | /etc/flashmq/flashmq.conf             | /data/keys/mosquitto.key, /data/keys/mosquitto.crt           |

You can update those files to set your own certificates.  
As they are not in */data/* folder, they will be reset during every firmware ugrades.

To make those change persistent, [install mod-persist](./VenusOS-Mod_persist.md.md#how-to-install-it) then create a patch file for each configuration file.  
For example, for the Gui :

``` bash
# Duplicate conf file
cp /etc/nginx/sites-available/https.site /etc/nginx/sites-available/https.site.ori

# Replace default certificates with your own
sed -i 's|/data/etc/ssl/venus.local.key|/data/etc/ssl/your-cert-key.pem|' /etc/nginx/sites-available/https.site
sed -i 's|/data/etc/ssl/venus.local.crt|/data/etc/ssl/your-cert.pem|' /etc/nginx/sites-available/https.site

# Create patch file
mkdir -p /data/etc/nginx/sites-available/
diff /etc/nginx/sites-available/https.site.ori /etc/nginx/sites-available/https.site > /data/etc/nginx/sites-available/https.site.patch

# Revert changes to apply them with mod-persist patch script
rm /etc/nginx/sites-available/https.site
mv /etc/nginx/sites-available/https.site.ori /etc/nginx/sites-available/https.site
persist-patch install /data/etc/nginx/sites-available/https.site.patch
```

### Reboot

Reboot to load new certificates
``` bash
    reboot
```