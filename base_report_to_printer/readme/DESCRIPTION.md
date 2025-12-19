This module provides the core framework to send Odoo reports directly to printers.
It defines the base models, configuration options and printing workflow, without depending on a specific printing protocol.

The actual connection with printers is delegated to extension modules (e.g. base_report_to_printer_cups), which implement support for a given printing backend.

Key features:

Flexible report output behavior:

Send to Client (default): generates a downloadable PDF.

Send to Printer: sends the report directly to a configured printer (via backend module).

Support for user-level, report-level, and combined user/report printing rules.

Extensible design: new modules can add support for additional printing systems or protocols.

This modular approach allows administrators to configure printing globally, per user, per report, or per user/report combination, while keeping the printing backend independent and replaceable.
