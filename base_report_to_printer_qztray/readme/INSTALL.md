This module requires **QZ Tray** to be installed and properly configured on the client machine, as well as additional setup on the Odoo server to enable secure communication.

## Prerequisites

### 1. Install QZ Tray on the client

Download and install QZ Tray on every client that will send print jobs:

https://qz.io/download/

Make sure QZ Tray is running before attempting to print from Odoo.

---

### 2. Install pyOpenSSL on the Odoo server

`pyOpenSSL` is required to sign the messages sent to QZ Tray.
This avoids security warnings and allows trusted communication.

```bash
sudo pip3 install pyOpenSSL
```

If you are using a virtual environment, make sure to install it inside that environment.

### 3. Generate a signing certificate
Generate a self-signed certificate that will be used by Odoo to sign QZ Tray messages.


When prompted for:
```bash
Common Name (e.g. server FQDN or YOUR name) []:
```
You must enter your Odoo domain name.

You can also use a wildcard domain, for example:
```
*.my-odoo-domain.com
```
Generate the certificate with:
```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 3650 -nodes
```

This will generate two files:

***cert.pem*** → public certificate

***key.pem*** → private key

### 4. Configure the certificate in Odoo
Log in to Odoo with administrator privileges and enable developer mode.
Then go to:
* **Settings -> Technical -> Parameters -> System Parameters**

Create the following parameters:

| **Key**        | **Value**                       |
|----------------|---------------------------------|
| qz.certificate | Content of cert.pem (full text) |
| qz.key         | Content of key.pem (full text)  |

Make sure to copy the full contents, including the BEGIN and END lines.

### 5. Install the certificate in QZ Tray (client side)
On the client machine:

1. Open the QZ Tray menu.

2. Go to Advanced → Site Manager.

3. Drag and drop the cert.pem file into the Site Manager.

4. Ensure the certificate is associated with your Odoo domain.

This step authorizes your Odoo server to send signed print jobs to QZ Tray.

### Notes

- Each client machine must have QZ Tray installed and running.
- The certificate must match the domain used to access Odoo.
- The same certificate can be used in all client machines.
- This module is designed to be backend-agnostic and works together with other base_report_to_printer_* backends.
