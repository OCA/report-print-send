Once configured, printing works transparently. When a user prints a
report that is set to *Send to Printer* and the assigned printer uses the
**WebSocket** backend, the module will:

1. Render the report, as PDF or as text (e.g. ZPL labels).
2. Encode the content in Base64.
3. Send a ``print_job`` message through the bus to the printer's
   configured user with the following payload

       {
           "printer_name": "<system_name of the printer>",
           "file_data": "<base64-encoded PDF>",
           "file_type": "qweb-pdf",
           "job_uuid": "<id of the printing job>"
       }

Each message creates a *Printing Job* in state Pending. The agent reports
back when the job leaves its CUPS queue by posting, as the printer's
user, a JSON-RPC call to ``/printing/websocket/job/state`` with
``job_uuid``, ``state`` (``processing``, ``completed``, ``canceled`` or
``aborted``), and optionally ``cups_job_id`` and ``reason`` (a CUPS
``job-state-reasons`` keyword). When the job reaches a final state, the
method ``_websocket_finished`` of the job is called, for other modules
to act on it. A completed job means CUPS handed the whole document to
the printer, not that the paper came out.

Text reports are handled too: the base module leaves them to the
browser download, so this module registers its own report handler that
sends them to the printer instead. The ``file_type`` key of the payload
tells the agent which kind of content it receives.

The recommended client-side agent is
`odoo-print-client <https://pypi.org/project/odoo-print-client/>`_,
which connects as the configured user and forwards jobs to the local printer.