# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.addons.base_report_to_printer.tests.test_report import TestReport


class TestReportWebSocket(TestReport):
    def new_printer(self):
        return self.env["printing.printer"].create(
            {
                "name": "WebSocket Printer",
                "system_name": "ws_printer",
                "backend": "websocket",
                "websocket_user_id": self.env.user.id,
                "default": True,
                "status": "available",
            }
        )

    def test_render_qweb_pdf_printable(self):
        """Override: mock bus._sendone instead of print_document for websocket."""
        with mock.patch.object(
            type(self.env["bus.bus"]),
            "_sendone",
        ) as mock_sendone:
            self.report.property_printing_action_id.action_type = "server"
            printer = self.new_printer()
            self.report.printing_printer_id = printer
            self.report._render_qweb_pdf(self.report.report_name, self.partners.ids)
            mock_sendone.assert_called_once()
            call_args = mock_sendone.call_args
            self.assertEqual(call_args[0][0], printer)
            self.assertEqual(call_args[0][1], "print_job")
            payload = call_args[0][2]
            self.assertIn("file_data", payload)
            self.assertIn("printer_name", payload)

    def test_render_qweb_text_printable(self):
        """Override: mock bus._sendone instead of print_document for websocket."""
        with mock.patch.object(
            type(self.env["bus.bus"]),
            "_sendone",
        ) as mock_sendone:
            self.report_text.property_printing_action_id.action_type = "server"
            printer = self.new_printer()
            self.report_text.printing_printer_id = printer
            self.report_text._render_qweb_text(
                self.report_text.report_name, self.partners.ids
            )
            mock_sendone.assert_called_once()
            payload = mock_sendone.call_args[0][2]
            self.assertIn("file_data", payload)

    def test_print_document_not_printable(self):
        """Override: use websocket printer."""
        self.report.printing_printer_id = self.new_printer()
        with mock.patch.object(
            type(self.env["bus.bus"]),
            "_sendone",
        ) as mock_sendone:
            self.report.print_document(self.partners.ids)
            mock_sendone.assert_called_once()

    def test_print_document_printable(self):
        """Override: use websocket printer."""
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_printer()
        with mock.patch.object(
            type(self.env["bus.bus"]),
            "_sendone",
        ) as mock_sendone:
            self.report.print_document(self.partners.ids)
            mock_sendone.assert_called_once()

    def test_print_document_string(self):
        """Override: websocket handles string content directly."""
        with mock.patch.object(
            type(self.env["bus.bus"]),
            "_sendone",
        ) as mock_sendone:
            printer = self.new_printer()
            printer.print_document("", "test")
            mock_sendone.assert_called_once()
