This module extends *base_report_to_printer* to send print jobs directly to
network printers over a raw TCP socket (typically port 9100), bypassing CUPS.
It is intended for ZPL label printers and other devices that accept a raw byte
stream.
