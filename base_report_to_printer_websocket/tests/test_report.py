# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from unittest import mock

from odoo.tests import Form

from odoo.addons.base_report_to_printer.tests.test_report import TestReport


class TestReportWebSocket(TestReport):
    def new_printer(self):
        return self.env["printing.printer"].create(
            {
                "name": "WebSocket Printer",
                "server_id": self.server.id,
                "system_name": "ws_printer",
                "backend": "websocket",
                "websocket_user_id": self.env.user.id,
                "default": True,
                "status": "available",
            }
        )

    def test_render_qweb_pdf_printable(self):
        """Override: mock bus._sendone instead of print_document for websocket."""
        with (
            mock.patch.object(
                type(self.env["bus.bus"]),
                "_sendone",
            ) as mock_sendone,
            self.assertLogs(level=logging.WARNING),
        ):
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
        with (
            mock.patch.object(
                type(self.env["bus.bus"]),
                "_sendone",
            ) as mock_sendone,
            self.assertLogs(level=logging.WARNING),
        ):
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
        with (
            mock.patch.object(
                type(self.env["bus.bus"]),
                "_sendone",
            ) as mock_sendone,
            self.assertLogs(level=logging.WARNING),
        ):
            self.report.print_document(self.partners.ids)
            mock_sendone.assert_called_once()

    def test_print_document_printable(self):
        """Override: use websocket printer."""
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_printer()
        with (
            mock.patch.object(
                type(self.env["bus.bus"]),
                "_sendone",
            ) as mock_sendone,
            self.assertLogs(level=logging.WARNING),
        ):
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

    def new_websocket_printer(self, **vals):
        return self.env["printing.printer"].create(
            {
                "name": "WebSocket Printer",
                "system_name": "ws_printer",
                "backend": "websocket",
                "websocket_user_id": self.env.user.id,
                "default": True,
                **vals,
            }
        )

    def test_behaviour_websocket_printer_no_exception(self):
        """A WebSocket printer has no server to reach and must not be flagged."""
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_websocket_printer()
        report = self.report.with_context(skip_printer_exception=False)
        with self.assertNoLogs(level=logging.WARNING):
            behaviour = report.behaviour()
        self.assertEqual(behaviour["action"], "server")
        self.assertNotIn("printer_exception", behaviour)

    def test_behaviour_websocket_printer_status_exception(self):
        """Only its status can flag a WebSocket printer."""
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_websocket_printer(
            status="unavailable"
        )
        report = self.report.with_context(skip_printer_exception=False)
        self.assertTrue(report.behaviour().get("printer_exception"))

    def test_behaviour_cups_printer_still_checked(self):
        """The connection check of the base module is kept for CUPS printers."""
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.env["printing.printer"].create(
            {
                "name": "CUPS Printer",
                "system_name": "cups_printer",
                "backend": "cups",
                "server_id": self.server.id,
            }
        )
        report = self.report.with_context(skip_printer_exception=False)
        with self.assertLogs(level=logging.WARNING):
            behaviour = report.behaviour()
        self.assertTrue(behaviour.get("printer_exception"))

    def test_print_action_for_report_name_backend(self):
        """The browser needs the backend to know which handler applies."""
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_websocket_printer()
        result = self.env["ir.actions.report"].print_action_for_report_name(
            self.report.report_name
        )
        self.assertEqual(result["action"], "server")
        self.assertEqual(result["backend"], "websocket")
        self.assertNotIn("printer_exception", result)

    def test_render_qweb_text_sends_job_without_skip_context(self):
        """A text report reaches the bus without the exception being skipped."""
        self.report_text.property_printing_action_id.action_type = "server"
        self.report_text.printing_printer_id = self.new_websocket_printer()
        report = self.report_text.with_context(skip_printer_exception=False)
        with mock.patch.object(type(self.env["bus.bus"]), "_sendone") as mock_sendone:
            report._render_qweb_text(report.report_name, self.partners.ids)
        mock_sendone.assert_called_once()

    def test_onchange_backend_clears_server(self):
        """Switching a printer to WebSocket drops the server it no longer needs."""
        with Form(self.env["printing.printer"]) as form:
            form.name = "Printer"
            form.system_name = "sys_name"
            form.server_id = self.server
            form.backend = "websocket"
            form.websocket_user_id = self.env.user
            self.assertFalse(form.server_id)
