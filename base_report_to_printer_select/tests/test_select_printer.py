# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo import exceptions
from odoo.tests.common import TransactionCase

PRINTER_MODEL = "odoo.addons.base_report_to_printer.models.printing_printer"
SERVER_MODEL = "odoo.addons.base_report_to_printer.models.printing_server"


class TestSelectPrinter(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Models
        cls.Report = cls.env["ir.actions.report"]
        cls.XmlAction = cls.env["printing.report.xml.action"]
        # Existing instances
        cls.format_a4 = cls.env.ref("base.paperformat_euro")
        cls.format_letter = cls.env.ref("base.paperformat_us")
        cls.partner = cls.env.ref("base.main_partner")
        # Instances
        cls.server = cls.env["printing.server"].create({})
        cls.printer_any = cls._create_printer("Any format")
        cls.printer_a4 = cls._create_printer("A4 only", cls.format_a4)
        cls.printer_letter = cls._create_printer("Letter only", cls.format_letter)
        cls.action_select = cls.env["printing.action"].create(
            {"name": "Ask", "action_type": "select"}
        )
        cls.report = cls._create_report()
        # Setup
        cls.env.company.paperformat_id = cls.format_letter

    @classmethod
    def _create_printer(cls, name, paperformat=None, **kwargs):
        values = {
            "name": name,
            "system_name": name,
            "server_id": cls.server.id,
            "status": "available",
            "paperformat_ids": [(6, 0, paperformat.ids)] if paperformat else False,
        }
        values.update(kwargs)
        return cls.env["printing.printer"].create(values)

    @classmethod
    def _create_report(cls, **kwargs):
        view = cls.env["ir.ui.view"].create(
            {
                "name": "Select printer test",
                "type": "qweb",
                "arch": """<t t-name="base_report_to_printer_select.test_text">
                Test
                </t>""",
            }
        )
        cls.env["ir.model.data"].create(
            {
                "name": "test_text",
                "module": "base_report_to_printer_select",
                "model": "ir.ui.view",
                "res_id": view.id,
            }
        )
        values = {
            "name": "Select printer test",
            "model": "res.partner",
            "report_type": "qweb-text",
            "report_name": "base_report_to_printer_select.test_text",
            "paperformat_id": cls.format_a4.id,
            "property_printing_action_id": cls.action_select.id,
        }
        values.update(kwargs)
        return cls.Report.create(values)

    def test_select_action_type(self):
        self.assertIn(
            "select",
            [code for code, _ in self.env["printing.action"]._available_action_types],
        )
        selection = self.XmlAction._fields["action"]._description_selection(self.env)
        self.assertIn("select", dict(selection))

    def test_candidate_printers_by_paperformat(self):
        self.assertEqual(
            self.report._get_candidate_printers(), self.printer_any | self.printer_a4
        )
        self.report.paperformat_id = False
        self.assertEqual(
            self.report._get_candidate_printers(),
            self.printer_any | self.printer_letter,
        )
        self.env.company.paperformat_id = False
        self.assertEqual(self.report._get_candidate_printers(), self.printer_any)

    def test_behaviour_select_ignores_printer_exception(self):
        self.report.printing_printer_id = self.printer_a4
        self.printer_a4.status = "error"
        with mock.patch(f"{SERVER_MODEL}.cups"):
            behaviour = self.report.behaviour()
        self.assertEqual(behaviour["action"], "select")
        self.assertEqual(behaviour["printer"], self.printer_a4)
        self.assertNotIn("printer_exception", behaviour)

    def test_print_action_for_report_name(self):
        self.report.printing_printer_id = self.printer_a4
        self.printer_a4.status = "error"
        with mock.patch(f"{SERVER_MODEL}.cups"):
            result = self.Report.print_action_for_report_name(self.report.report_name)
        self.assertEqual(result["action"], "select")
        self.assertNotIn("printer_exception", result)
        printers = {printer["id"]: printer for printer in result["printers"]}
        self.assertEqual(set(printers), set((self.printer_any | self.printer_a4).ids))
        self.assertEqual(printers[self.printer_a4.id]["status"], "error")
        self.assertEqual(result["printer_id"], self.printer_a4.id)
        self.report.printing_printer_id = self.printer_letter
        with mock.patch(f"{SERVER_MODEL}.cups"):
            result = self.Report.print_action_for_report_name(self.report.report_name)
        self.assertFalse(result["printer_id"])

    def test_print_action_for_report_name_other_action(self):
        self.report.property_printing_action_id = self.env["printing.action"].create(
            {"name": "Server", "action_type": "server"}
        )
        self.report.printing_printer_id = self.printer_a4
        with mock.patch(f"{SERVER_MODEL}.cups"):
            result = self.Report.print_action_for_report_name(self.report.report_name)
        self.assertEqual(result["action"], "server")
        self.assertNotIn("printers", result)

    def test_print_document_select(self):
        with (
            mock.patch(f"{SERVER_MODEL}.cups"),
            mock.patch(
                f"{PRINTER_MODEL}.PrintingPrinter.print_document", autospec=True
            ) as print_document,
        ):
            self.assertTrue(
                self.report.print_document_select(self.partner.ids, self.printer_any.id)
            )
        print_document.assert_called_once()
        self.assertEqual(print_document.call_args.args[0], self.printer_any)
        self.assertEqual(print_document.call_args.args[1], self.report)
        line = self.XmlAction.search(
            [("report_id", "=", self.report.id), ("user_id", "=", self.env.uid)]
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.action, "select")
        self.assertEqual(line.printer_id, self.printer_any)
        with mock.patch(f"{SERVER_MODEL}.cups"):
            self.assertEqual(self.report.behaviour()["printer"], self.printer_any)
        with (
            mock.patch(f"{SERVER_MODEL}.cups"),
            mock.patch(
                f"{PRINTER_MODEL}.PrintingPrinter.print_document", autospec=True
            ) as print_document,
        ):
            self.report.print_document_select(self.partner.ids, self.printer_a4.id)
        self.assertEqual(print_document.call_args.args[0], self.printer_a4)
        self.assertEqual(
            self.XmlAction.search(
                [("report_id", "=", self.report.id), ("user_id", "=", self.env.uid)]
            ),
            line,
        )
        self.assertEqual(line.printer_id, self.printer_a4)

    def test_print_document_select_as_user(self):
        user = self.env["res.users"].create(
            {
                "name": "Printing user",
                "login": "printing_user",
                "groups_id": [(6, 0, self.env.ref("base.group_user").ids)],
            }
        )
        report = self.report.with_user(user)
        with (
            mock.patch(f"{SERVER_MODEL}.cups"),
            mock.patch(
                f"{PRINTER_MODEL}.PrintingPrinter.print_document", autospec=True
            ) as print_document,
        ):
            self.assertTrue(
                report.print_document_select(self.partner.ids, self.printer_any.id)
            )
        self.assertEqual(print_document.call_args.args[0], self.printer_any)
        line = self.XmlAction.search([("report_id", "=", self.report.id)])
        self.assertEqual(line.user_id, user)
        self.assertEqual(line.printer_id, self.printer_any)

    def test_print_document_select_keeps_user_action(self):
        line = self.XmlAction.create(
            {
                "report_id": self.report.id,
                "user_id": self.env.uid,
                "action": "client",
            }
        )
        with (
            mock.patch(f"{SERVER_MODEL}.cups"),
            mock.patch(
                f"{PRINTER_MODEL}.PrintingPrinter.print_document", autospec=True
            ) as print_document,
        ):
            self.report.print_document_select(self.partner.ids, self.printer_a4.id)
        self.assertEqual(print_document.call_args.args[0], self.printer_a4)
        self.assertEqual(line.action, "client")
        self.assertFalse(line.printer_id)

    def test_print_document_select_wrong_printer(self):
        with self.assertRaises(exceptions.UserError):
            self.report.print_document_select(self.partner.ids, self.printer_letter.id)
