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

| Tool     | File                                  | Default certificates                                          |
| -------- | ------------------------------------- | ------------------------------------------------------------- |
| Gui      | /etc/nginx/sites-available/https.site | /data/etc/ssl/venus.local.key; /data/etc/ssl/venus.local.crt; |
| Node-RED | /etc/nginx/sites-available/node-red   | /data/etc/ssl/venus.local.key; /data/etc/ssl/venus.local.crt; |
| FlashMQ  | /etc/flashmq/flashmq.conf             | /data/keys/mosquitto.key; /data/keys/mosquitto.crt            |

You can update the files above to set your own certificates but as there are not in */data/* folder, you would have to do it after every firmware ugrades.

If you are fine with having the same certificate for the 3 tools, easiest way is to set links in the */data/* folders :

```bash
mv /data/etc/ssl/venus.local.key /data/etc/ssl/venus.local.key.bak
mv /data/etc/ssl/venus.local.crt /data/etc/ssl/venus.local.crt.bak
ln -s /data/etc/ssl/your-cert-key.pem /data/etc/ssl/venus.local.key
ln -s  /data/etc/ssl/your-cert.pem /data/etc/ssl/venus.local.crt

mv /data/keys/mosquitto.key /data/keys/mosquitto.key.bak
mv /data/keys/mosquitto.crt /data/keys/mosquitto.crt.bak
ln -s /data/etc/ssl/your-cert-key.pem /data/keys/mosquitto.key
ln -s /data/etc/ssl/your-cert.pem /data/keys/mosquitto.crt
```

### Reboot

Reboot to load new certificates
``` bash
    reboot
```