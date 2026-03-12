# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from base64 import b64encode
from unittest import mock

from odoo.addons.base_report_to_printer.tests.test_printing_printer import (
    TestPrintingPrinterBase,
)


class TestPrintingPrinterWebSocket(TestPrintingPrinterBase):
    def setUp(self):
        super().setUp()
        self.printer_vals.update(
            {
                "backend": "websocket",
                "websocket_user_id": self.env.user.id,
            }
        )

    def test_print_document_sends_to_bus(self):
        """print_document should encode PDF as base64 and send via bus."""
        printer = self.new_record()
        report = self.env["ir.actions.report"].search([], limit=1)
        content = b"%PDF-1.4 test content"
        with mock.patch.object(
            type(self.env["bus.bus"]),
            "_sendone",
        ) as mock_sendone:
            result = printer.print_document(report, content)
            self.assertTrue(result)
            mock_sendone.assert_called_once()
            call_args = mock_sendone.call_args
            self.assertEqual(call_args[0][0], printer)
            self.assertEqual(call_args[0][1], "print_job")
            payload = call_args[0][2]
            self.assertEqual(payload["printer_name"], printer.system_name)
            self.assertEqual(payload["file_data"], b64encode(content).decode("utf-8"))

    def test_print_document_string_content(self):
        """print_document should handle string content by encoding to UTF-8."""
        printer = self.new_record()
        report = self.env["ir.actions.report"].search([], limit=1)
        content = "string content"
        with mock.patch.object(
            type(self.env["bus.bus"]),
            "_sendone",
        ) as mock_sendone:
            result = printer.print_document(report, content)
            self.assertTrue(result)
            payload = mock_sendone.call_args[0][2]
            expected_b64 = b64encode(content.encode("utf-8")).decode("utf-8")
            self.assertEqual(payload["file_data"], expected_b64)

    def test_print_document_non_websocket_delegates_to_super(self):
        """Non-websocket printers should use the base print_document flow."""
        self.printer_vals["backend"] = "base"
        printer = self.new_record()
        report = self.env["ir.actions.report"].search([], limit=1)
        with mock.patch.object(
            type(self.env["bus.bus"]),
            "_sendone",
        ) as mock_sendone:
            with mock.patch.object(
                type(self.env["printing.printer"]),
                "print_file",
            ):
                printer.print_document(report, b"test")
            mock_sendone.assert_not_called()

    def test_print_document_empty_system_name(self):
        """When system_name is empty, printer_name in payload should be empty."""
        self.printer_vals["system_name"] = ""
        printer = self.new_record()
        report = self.env["ir.actions.report"].search([], limit=1)
        with mock.patch.object(
            type(self.env["bus.bus"]),
            "_sendone",
        ) as mock_sendone:
            printer.print_document(report, b"test")
            payload = mock_sendone.call_args[0][2]
            self.assertEqual(payload["printer_name"], "")

    def test_print_document_sends_to_printer_record(self):
        """print_document should send the bus message to the printer record."""
        printer = self.new_record()
        report = self.env["ir.actions.report"].search([], limit=1)
        with mock.patch.object(
            type(self.env["bus.bus"]),
            "_sendone",
        ) as mock_sendone:
            printer.print_document(report, b"test")
            self.assertEqual(mock_sendone.call_args[0][0], printer)
