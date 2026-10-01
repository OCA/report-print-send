# QZ Tray Printing Backend

This module adds support for printing Odoo reports directly from the client machine using **QZ Tray** as a printing backend.

It allows reports to be sent securely to locally installed printers without relying on server-side printing systems such as CUPS. Instead, printing is handled on the client side through QZ Tray, enabling direct access to USB, network, or system printers.

This backend is especially useful in environments where client-side printing is required, such as Point of Sale setups, kiosk systems, or deployments where the Odoo server does not have access to the printers used by end users.
