# Configuring SSL certificates

* [Adding root CA](#adding-root-ca)
* [Replacing Victron SSL default certificate](#replacing-victron-ssl-default-certificate)

## Adding root CAs

Append your root CA to `/etc/ssl/certs/ca-certificates.crt`.

> [!NOTE]  
> This configuration file is not in the `/data` folder, hence it will be overwritten by Venus OS updates.

## Replacing Victron SSL default certificate

### Copy your certificate

Copy your certificate and its private key to `/data/etc/ssl`, grant them appropriated rights :

``` bash
    chmod 644 /data/etc/ssl/your-cert.pem
    chmod 400 /data/etc/ssl/your-cert-key.pem
```

> [!NOTE]  
> Those files are in the `/data` folder, hence they will survive Venus OS updates.

### Update SSL configuration

| Tool     | File                                  | Before                                                                                                                                                                                      | After                                                                                                                                                                                       |
|----------|---------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| NGinx    | /etc/nginx/sites-available/https.site | server {<br />&emsp;listen 443 ssl;<br />&emsp;listen [::]:443 ssl;<br />&emsp;ssl_certificate /data/etc/ssl/venus.local.crt;<br />&emsp;ssl_certificate_key /data/etc/ssl/venus.local.key; | server {<br />&emsp;listen 443 ssl;<br />&emsp;listen [::]:443 ssl;<br />&emsp;ssl_certificate /data/etc/ssl/your-cert.pem;<br />&emsp;ssl_certificate_key /data/etc/ssl/your-cert-key.pem; |
| Node-RED | /etc/nginx/sites-available/node-red   | server {<br />&emsp;listen 1881 ssl;<br />&emsp;server_name _;<br />&emsp;ssl_certificate /data/etc/ssl/venus.local.crt;<br />&emsp;ssl_certificate_key /data/etc/ssl/venus.local.key;      | server {<br />&emsp;listen 1881 ssl;<br />&emsp;server_name _;<br />&emsp;ssl_certificate /data/etc/ssl/your-cert.pem;<br />&emsp;ssl_certificate_key /data/etc/ssl/your-cert-key.pem;      |
| FlashMQ  | /etc/flashmq/flashmq.conf             | listen {<br />&emsp;protocol mqtt<br />&emsp;port 8883<br />&emsp;fullchain /data/keys/mosquitto.crt<br />&emsp;privkey /data/keys/mosquitto.key<br />}                                     | listen {<br />&emsp;protocol mqtt<br />&emsp;port 8883<br />&emsp;fullchain /data/etc/ssl/your-cert.pem<br />&emsp;privkey /data/etc/ssl/your-cert-key.pem<br />}                           |

> [!NOTE]  
> Those configuration file are not in the `/data` folder, they will be overwritten by Venus OS updates, you will need to redo this configuration after every update.

### Reboot

``` bash
    reboot
```