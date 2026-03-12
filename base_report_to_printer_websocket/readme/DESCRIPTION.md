This module extends *base_report_to_printer* to send print jobs through
the Odoo Bus (WebSocket) instead of a traditional print server like CUPS.

When a report is printed, the module encodes the rendered PDF in Base64
and sends a ``print_job`` message through the bus to the user configured
on the printer. A client-side listener running as that user receives
the payload and forwards it to the local printer.

Main features:

- No external print server required — works over the existing Odoo Bus.
- Sends print jobs as Base64-encoded PDFs via WebSocket.
- Each printer is bound to a specific Odoo user, so jobs are delivered
  only to the right client-side agent.
- Compatible with the standard *base_report_to_printer* configuration
  (global, per user, per report, per user + report).
- Works with `odoo-print-client <https://pypi.org/project/odoo-print-client/>`_
  as the client-side agent to receive and print jobs.
