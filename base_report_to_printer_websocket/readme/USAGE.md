Once configured, printing works transparently. When a user prints a
report that is set to *Send to Printer* and the assigned printer uses the
**WebSocket** backend, the module will:

1. Render the report, as PDF or as text (e.g. ZPL labels).
2. Encode the content in Base64.
3. Send a ``print_job`` message through the bus to the printer's
   configured user with the following payload

       {
           "printer_name": "<system_name of the printer>",
           "file_data": "<base64-encoded PDF>"
       }

Text reports are handled too: the base module leaves them to the
browser download, so this module registers its own report handler that
sends them to the printer instead. The ``file_type`` key of the payload
tells the agent which kind of content it receives.

The recommended client-side agent is
`odoo-print-client <https://pypi.org/project/odoo-print-client/>`_,
which connects as the configured user and forwards jobs to the local printer.