# Copyright 2016 LasLabs Inc.
# Copyright 2017 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo import exceptions
from odoo.tests import common


class TestReport(common.HttpCase):
    def setUp(self):
        super(TestReport, self).setUp()
        self.Model = self.env["ir.actions.report"]
        self.server = self.env["printing.server"].create({})
        self.report_vals = {
            "name": "Test Report",
            "model": "ir.actions.report",
            "report_name": "Test Report",
        }
        self.report_view = self.env["ir.ui.view"].create(
            {
                "name": "Test",
                "type": "qweb",
                "arch": """<t t-name="base_report_to_printer.test">
                <div>Test</div>
            </t>""",
            }
        )
        self.report_imd = (
            self.env["ir.model.data"]
            .sudo()
            .create(
                {
                    "name": "test",
                    "module": "base_report_to_printer",
                    "model": "ir.ui.view",
                    "res_id": self.report_view.id,
                }
            )
        )
        self.report = self.Model.create(
            {
                "name": "Test",
                "report_type": "qweb-pdf",
                "model": "res.partner",
                "report_name": "base_report_to_printer.test",
            }
        )
        self.report_text = self.Model.create(
            {
                "name": "Test",
                "report_type": "qweb-text",
                "model": "res.partner",
                "report_name": "base_report_to_printer.test",
            }
        )
        self.partners = self.env["res.partner"]
        for n in range(5):
            self.partners += self.env["res.partner"].create({"name": "Test %d" % n})

    def new_record(self):
        return self.Model.create(self.report_vals)

    def new_printer(self):
        return self.env["printing.printer"].create(
            {
                "name": "Printer",
                "server_id": self.server.id,
                "system_name": "Sys Name",
                "default": True,
                "status": "unknown",
                "status_message": "Msg",
                "model": "res.users",
                "location": "Location",
                "uri": "URI",
            }
        )

    def test_can_print_report_context_skip(self):
        """It should return False based on context"""
        rec_id = self.new_record().with_context(must_skip_send_to_printer=True)
        res = rec_id._can_print_report({"action": "server"}, True, True)
        self.assertFalse(res)

    def test_can_print_report_true(self):
        """It should return True when server print allowed"""
        res = self.new_record()._can_print_report({"action": "server"}, True, True)
        self.assertTrue(res)

    def test_can_print_report_false(self):
        """It should return False when server print not allowed"""
        res = self.new_record()._can_print_report({"action": "server"}, True, False)
        self.assertFalse(res)

    def test_render_qweb_pdf_not_printable(self):
        """It should print the report, only if it is printable"""
        with mock.patch(
            "odoo.addons.base_report_to_printer.models."
            "printing_printer.PrintingPrinter."
            "print_document"
        ) as print_document:
            self.report._render_qweb_pdf(self.report.report_name, self.partners.ids)
            print_document.assert_not_called()

    def test_render_qweb_pdf_printable(self):
        """It should print the report, only if it is printable"""
        with mock.patch(
            "odoo.addons.base_report_to_printer.models."
            "printing_printer.PrintingPrinter."
            "print_document"
        ) as print_document:
            self.report.property_printing_action_id.action_type = "server"
            self.report.printing_printer_id = self.new_printer()
            document = self.report._render_qweb_pdf(
                self.report.report_name, self.partners.ids
            )
            print_document.assert_called_once_with(
                self.report,
                document[0],
                action="server",
                doc_format="qweb-pdf",
                tray=False,
            )

    def test_render_qweb_text_printable(self):
        """It should print the report, only if it is printable"""
        with mock.patch(
            "odoo.addons.base_report_to_printer.models."
            "printing_printer.PrintingPrinter."
            "print_document"
        ) as print_document:
            self.report_text.property_printing_action_id.action_type = "server"
            self.report_text.printing_printer_id = self.new_printer()
            document = self.report_text._render_qweb_text(
                self.report.report_name, self.partners.ids
            )
            print_document.assert_called_once_with(
                self.report_text,
                document[0],
                action="server",
                doc_format="qweb-text",
                tray=False,
            )

    def test_print_document_not_printable(self):
        """It should print the report, regardless of the defined behaviour"""
        self.report.printing_printer_id = self.new_printer()
        with mock.patch(
            "odoo.addons.base_report_to_printer.models."
            "printing_printer.PrintingPrinter."
            "print_document"
        ) as print_document:
            self.report.print_document(self.partners.ids)
            print_document.assert_called_once()

    def test_print_document_printable(self):
        """It should print the report, regardless of the defined behaviour"""
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_printer()
        with mock.patch(
            "odoo.addons.base_report_to_printer.models."
            "printing_printer.PrintingPrinter."
            "print_document"
        ) as print_document:
            self.report.print_document(self.partners.ids)
            print_document.assert_called_once()

    def test_print_document_no_printer(self):
        """It should raise an error"""
        with self.assertRaises(exceptions.UserError):
            self.report.print_document(self.partners.ids)
