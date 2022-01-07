To install this module, you need to:

#. Install QZ Tray on client - https://qz.io/download/

#. Install pyOpenSSL

PyOpenSSL is required to sign messages sent to the clients QZ Tray (and prevent warnings).

.. code-block:: bash

   sudo pip3 install pyOpenSSL

#. Generate a certificate

Take care about "Common Name (e.g. server FQDN or YOUR name) []:" THIS ENTRY IS IMPORTANT,
this should be your Odoo domain name, can be filled in wildcard format an example of this would be \*.my-odoo-domain.com

.. code-block:: bash

   openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 3650-nodes

#. Set key and certificate on Odoo

Go to /Settings/Technical/Parameters/System Parameters and set:
- a parameter called qz.certificate with the content of the certificate.
- a parameter called qz.key with the content of the key.


#. Install certificate on client QZ Tray.

Open QZ Tray menu /Advanced/Site Manager and drag and drop cert.pem for your Odoo domain.
