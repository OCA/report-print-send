# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestPrintingPrinterBase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Model = self.env["printing.printer"]
        self.printer_vals = {
            "name": "Printer",
            "system_name": "Sys Name",
            "default": True,
            "status": "unknown",
            "status_message": "Msg",
            "model": "res.users",
            "location": "Location",
            "uri": "URI",
        }

    def new_record(self):
        return self.Model.create(self.printer_vals)

    def test_option_tray(self):
        self.assertEqual(
            self.Model._set_option_input_tray(None, "Test Tray"),
            {"InputSlot": "Test Tray"},
        )
        self.assertEqual(self.Model._set_option_input_tray(None, False), {})

    def test_option_noops(self):
        self.assertEqual(self.Model._set_option_action(None, "printer"), {})
        self.assertEqual(self.Model._set_option_printer(None, self.Model), {})

    def test_option_doc_format(self):
        self.assertEqual(
            self.Model._set_option_doc_format(None, "raw"), {"raw": "True"}
        )
        self.assertEqual(self.Model._set_option_format(None, "raw"), {"raw": "True"})
        self.assertEqual(self.Model._set_option_doc_format(None, "pdf"), {})
        self.assertEqual(self.Model._set_option_format(None, "pdf"), {})

    def test_print_options(self):
        report = self.env["ir.actions.report"].search([], limit=1)
        self.assertEqual(self.Model.print_options(doc_format="raw"), {"raw": "True"})
        self.assertEqual(
            self.Model.print_options(report, doc_format="pdf", copies=2),
            {"copies": "2"},
        )
        self.assertEqual(
            self.Model.print_options(report, doc_format="raw", copies=2),
            {"raw": "True", "copies": "2"},
        )
        self.assertIn("InputSlot", self.Model.print_options(report, input_tray="Test"))

    def test_set_default_and_unset(self):
        printer = self.new_record()
        self.assertTrue(printer.default)
        other = self.new_record()
        other.set_default()
        self.assertFalse(printer.default)
        self.assertTrue(other.default)
        self.Model.set_default()
        self.assertEqual(other, self.Model.get_default())

        printer = self.new_record()
        self.assertTrue(printer.default)
        printer.unset_default()
        self.assertFalse(printer.default)
