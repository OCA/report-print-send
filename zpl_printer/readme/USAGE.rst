This module uses https connection to a printer in your network to print to it.
Assuming the printer is properly configured for this purpose, and in your network, for example as
`label.my_company.local` then the printer will wait for POST requests to https://label.my_company.local/pstprnt
So that would be the address that makes the printer available to Odoo.

To setup your printer for this, you have to provide a certificate and enable https on the printer,
which works with the following command, that you have to send to it:

::

    ~DYE:HTTPS_CERT.nrd,B,NRD,1480,,-----BEGIN CERTIFICATE-----
    THIS IS THE CONTENT OF YOUR CERTIFICATE, YOU HAVE TO CREATE IT
    -----END CERTIFICATE-----
    ~DYE:HTTPS_KEY.nrd,B,NRD,1704,,-----BEGIN PRIVATE KEY-----
    THIS IS THE CONTENT OF THE PRIVATE KEY FOR YOUR PRINTER, YOU HAVE TO CREATE IT
    -----END PRIVATE KEY-----
    ^XA
    ^JUS
    ^XZ
    ! U1 setvar "ip.https.enable" "on"
    ! U1 do "device.reset" ""

This might be done with a command like:

    cat your_cert_file.zpl > /dev/usb/lp1

Once everything is setup, the new printing option should be available eg. in the stock module to print serial numbers
with the option `Serial Number (Send to ZPL-Printer)`.
