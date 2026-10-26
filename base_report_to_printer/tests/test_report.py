# Copyright 2016 LasLabs Inc.
# Copyright 2017 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from unittest import mock

from odoo import exceptions
from odoo.tests import common

REPORT_TYPES = {"qweb-pdf": "pdf", "qweb-text": "text"}

server_model = "odoo.addons.base_report_to_printer.models.printing_server"


class TestReport(common.HttpCase):
    def setUp(self):
        super().setUp()
        self.Model = self.env["ir.actions.report"].with_context(
            skip_printer_exception=True
        )
        self.server = self.env["printing.server"].create({})
        self.report_vals = {
            "name": "Test Report",
            "model": "ir.actions.report",
            "report_name": "Test Report",
        }
        self.report_pdf_view = self.env["ir.ui.view"].create(
            {
                "name": "Test",
                "type": "qweb",
                "arch": """<t t-name="base_report_to_printer.test">
                <div>Test</div>
            </t>""",
            }
        )
        self.report_pdf_imd = (
            self.env["ir.model.data"]
            .sudo()
            .create(
                {
                    "name": "test_pdf",
                    "module": "base_report_to_printer",
                    "model": "ir.ui.view",
                    "res_id": self.report_pdf_view.id,
                }
            )
        )
        self.report_text_view = self.env["ir.ui.view"].create(
            {
                "name": "Test",
                "type": "qweb",
                "arch": """<t t-name="base_report_to_printer.test_text">
                Test
                </t>""",
            }
        )
        self.report_text_imd = (
            self.env["ir.model.data"]
            .sudo()
            .create(
                {
                    "name": "test_text",
                    "module": "base_report_to_printer",
                    "model": "ir.ui.view",
                    "res_id": self.report_text_view.id,
                }
            )
        )
        self.report = self.Model.create(
            {
                "name": "Test",
                "report_type": "qweb-pdf",
                "model": "res.partner",
                "report_name": "base_report_to_printer.test_pdf",
            }
        )
        self.report_text = self.Model.create(
            {
                "name": "Test",
                "report_type": "qweb-text",
                "model": "res.partner",
                "report_name": "base_report_to_printer.test_text",
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
        with (
            mock.patch(
                "odoo.addons.base_report_to_printer.models."
                "printing_printer.PrintingPrinter."
                "print_document"
            ) as print_document,
            self.assertLogs(level=logging.WARNING) as logs,
        ):
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
                input_tray=False,
                output_tray=False,
            )
            self.assertEqual(len(logs.records), 1)
            self.assertEqual(logs.records[0].levelno, logging.WARNING)

    def test_render_qweb_text_printable(self):
        """It should print the report, only if it is printable"""
        with (
            mock.patch(
                "odoo.addons.base_report_to_printer.models."
                "printing_printer.PrintingPrinter."
                "print_document"
            ) as print_document,
            self.assertLogs(level=logging.WARNING) as logs,
        ):
            self.report_text.property_printing_action_id.action_type = "server"
            self.report_text.printing_printer_id = self.new_printer()
            document = self.report_text._render_qweb_text(
                self.report_text.report_name, self.partners.ids
            )
            print_document.assert_called_once_with(
                self.report_text,
                document[0],
                action="server",
                doc_format="qweb-text",
                input_tray=False,
                output_tray=False,
            )
            self.assertEqual(len(logs.records), 1)
            self.assertEqual(logs.records[0].levelno, logging.WARNING)

    def test_print_document_not_printable(self):
        """It should print the report, regardless of the defined behaviour"""
        self.report.printing_printer_id = self.new_printer()
        with (
            mock.patch(
                "odoo.addons.base_report_to_printer.models."
                "printing_printer.PrintingPrinter."
                "print_document"
            ) as print_document,
            self.assertLogs(level=logging.WARNING) as logs,
        ):
            self.report.print_document(self.partners.ids)
            print_document.assert_called_once()
            self.assertEqual(len(logs.records), 2)
            self.assertEqual(logs.records[0].levelno, logging.WARNING)

    def test_print_document_printable(self):
        """It should print the report, regardless of the defined behaviour"""
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_printer()
        with (
            mock.patch(
                "odoo.addons.base_report_to_printer.models."
                "printing_printer.PrintingPrinter."
                "print_document"
            ) as print_document,
            self.assertLogs(level=logging.WARNING) as logs,
        ):
            self.report.print_document(self.partners.ids)
            print_document.assert_called_once()
            self.assertEqual(len(logs.records), 2)
            self.assertEqual(logs.records[0].levelno, logging.WARNING)

    def test_print_document_no_printer(self):
        """It should raise an error"""
        with self.assertRaises(exceptions.UserError):
            self.report.print_document(self.partners.ids)

    def test_print_document_string(self):
        """Test string encoding"""
        with mock.patch(
            "odoo.addons.base_report_to_printer.models."
            "printing_printer.PrintingPrinter."
            "print_file"
        ) as print_file:
            self.new_printer().print_document("", "test")
            print_file.assert_called_once()

    @mock.patch(f"{server_model}.cups")
    def test_print_document_printable_quantity(self, cups):
        """It should print the report, regardless of the defined behaviour"""
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_printer()
        report_type = REPORT_TYPES.get(self.report.report_type)
        behaviour = self.report.behaviour(**{"quantity": 3})
        behaviour.pop("printer")
        method_name = f"_render_qweb_{report_type}"
        document, doc_format = getattr(
            self.report.with_context(must_skip_send_to_printer=True), method_name
        )(self.report.report_name, self.partners.ids, data=None)
        behaviour["title"] = self.report.report_name
        behaviour["res_ids"] = self.partners.ids
        with mock.patch(
            "odoo.addons.base_report_to_printer.models."
            "printing_printer.PrintingPrinter."
            "print_document"
        ) as print_document:
            self.report.print_document(self.partners.ids, **{"quantity": 3})
            print_document.assert_called_once_with(
                self.report, document, doc_format=self.report.report_type, **behaviour
            )

    @mock.patch(f"{server_model}.cups")
    def test_print_document_printable_unknown(self, cups):
        """It should print the report, regardless of the defined behaviour"""
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_printer()
        report_type = REPORT_TYPES.get(self.report.report_type)
        behaviour = self.report.behaviour(**{"unknown": "test"})
        behaviour.pop("printer")
        method_name = f"_render_qweb_{report_type}"
        document, doc_format = getattr(
            self.report.with_context(must_skip_send_to_printer=True), method_name
        )(self.report.report_name, self.partners.ids, data=None)
        behaviour["title"] = self.report.report_name
        behaviour["res_ids"] = self.partners.ids
        with mock.patch(
            "odoo.addons.base_report_to_printer.models."
            "printing_printer.PrintingPrinter."
            "print_document"
        ) as print_document:
            self.report.print_document(self.partners.ids, **{"unknown": "test"})
            print_document.assert_called_once_with(
                self.report, document, doc_format=self.report.report_type, **behaviour
            )

    @mock.patch(f"{server_model}.cups")
    def test_behaviour_printer_extra_over_user_action(self, cups):
        """A forced printer wins over the user specific action"""
        user_printer = self.new_printer()
        forced_printer = self.new_printer()
        self.env["printing.report.xml.action"].create(
            {
                "report_id": self.report.id,
                "user_id": self.env.uid,
                "action": "server",
                "printer_id": user_printer.id,
            }
        )
        self.assertEqual(self.report.behaviour()["printer"], user_printer)
        self.assertEqual(
            self.report.behaviour(printer=forced_printer.id)["printer"],
            forced_printer,
        )

    @mock.patch(f"{server_model}.cups")
    def test_print_document_client_action_multi_thread_extras(self, cups):
        """The extras reach the thread that prints"""
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_printer()
        forced_printer = self.new_printer()
        forced_printer.multi_thread = True
        with mock.patch(
            "odoo.addons.base_report_to_printer.models.ir_actions_report.threading"
        ) as threading:
            self.assertTrue(
                self.report.print_document_client_action(
                    self.partners.ids, printer=forced_printer
                )
            )
            self.env.cr.postcommit.run()
        thread_kwargs = threading.Thread.call_args.kwargs
        self.assertEqual(thread_kwargs["args"][0], self.report.id)
        self.assertEqual(thread_kwargs["kwargs"], {"printer": forced_printer})
        threading.Thread.return_value.start.assert_called_once()

    def test_print_document_threaded_rebinds_extras(self):
        """A record given as extra is bound to the cursor of the thread"""
        forced_printer = self.new_printer()
        with mock.patch(
            "odoo.addons.base_report_to_printer.models.ir_actions_report."
            "IrActionsReport.print_document",
            autospec=True,
        ) as print_document:
            self.report.print_document_threaded(
                self.report.id, self.partners.ids, None, printer=forced_printer
            )
        args, kwargs = print_document.call_args
        report = args[0]
        self.assertEqual(report.id, self.report.id)
        self.assertIsNot(report.env.cr, self.env.cr)
        self.assertEqual(kwargs["printer"].id, forced_printer.id)
        self.assertIs(kwargs["printer"].env, report.env)

    @mock.patch(f"{server_model}.cups")
    def test_print_document_printer_extra(self, cups):
        """
        It should print the report to the desired printer
        """
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_printer()
        forced_printer = self.new_printer()
        forced_printer.system_name = "Forced Printer"
        report_type = REPORT_TYPES.get(self.report.report_type)
        behaviour = self.report.behaviour(**{"printer": forced_printer})
        behaviour.pop("printer")
        method_name = f"_render_qweb_{report_type}"
        document, doc_format = getattr(
            self.report.with_context(must_skip_send_to_printer=True), method_name
        )(self.report.report_name, self.partners.ids, data=None)
        behaviour["title"] = self.report.report_name
        behaviour["res_ids"] = self.partners.ids
        extras = {
            "printer": forced_printer,
        }
        self.report.print_document(self.partners.ids, **extras)
        self.assertEqual(
            "Forced Printer", cups.Connection().printFile.call_args.args[0]
        )
