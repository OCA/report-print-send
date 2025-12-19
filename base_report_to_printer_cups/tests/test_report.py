from odoo.addons.base_report_to_printer.tests.test_report import TestReport


class TestReportCups(TestReport):
    def setUp(self):
        super().setUp()
        # Ensure the printer uses CUPS backend and is in error state
        self.cups_server = self.env["printing.server"].create({"name": "CUPS Server"})
        # If base setUp created self.printer, attach it to the server
        if hasattr(self, "printer"):
            self.printer.write(
                {
                    "backend": "cups",
                    "status": "error",
                    "server_id": self.cups_server.id,
                }
            )
            self.report.write({"printing_printer_id": self.printer.id})

    def new_printer(self):
        # Always set server_id for CUPS printers
        return self.env["printing.printer"].create(
            {
                "name": "CUPS Printer",
                "system_name": "cups_printer",
                "backend": "cups",
                "status": "error",
                "server_id": self.cups_server.id,
            }
        )
