This module extends *base_report_to_printer* to add support for printing
reports through a CUPS server.

It allows users to configure one or more CUPS servers, automatically
fetch available printers and trays, and send reports directly to them
instead of downloading a PDF.

Main features:
- Manage CUPS servers from the Odoo backend.
- Synchronize available printers and trays with CUPS.
- Define default printing behavior globally, per user, per report, or
  per user and report.
- Test printer connectivity with a **Print Test Page** action.

Typical usage:
- Send reports directly to CUPS printers.
- Configure dedicated trays for pre-printed forms such as payment slips.
- Allow each user to define their own default printer preferences.
