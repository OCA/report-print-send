Configure a raw-socket printer under *Settings > Printing > Printers*:

1. Create a printer with backend **Raw Socket**.
2. Set **Host** to the printer IP address or hostname.
3. Leave **Port** at 9100 unless your device uses another raw port.
4. Assign the printer on reports, users, or calling code as with any other
   backend.

ZPL labels from ``printer_zpl2_odoonz`` call ``print_document`` with
``doc_format="raw"``; with this backend the generated ZPL is sent as UTF-8
bytes over the socket.
