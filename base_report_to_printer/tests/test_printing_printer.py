# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import new_test_user

from .common import ReportToPrinterCommon


class TestPrintingPrinterBase(ReportToPrinterCommon):
    def setUp(self):
        super().setUp()
        self.Model = self.env["printing.printer"]

    def new_record(self):
        return self.new_printer()

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

    def test_print_document_forwards_doc_format(self):
        """print_document passes the format on, so raw jobs stay raw."""
        printer = self.new_record()
        captured = {}

        def capture(self, file_name, report=None, **print_opts):
            captured["opts"] = print_opts
            captured["options"] = self.print_options(report=report, **print_opts)
            return True

        self.patch(type(printer), "print_file", capture)
        printer.print_document(None, b"^XA^XZ", doc_format="raw")
        self.assertEqual(captured["opts"], {"doc_format": "raw"})
        self.assertEqual(captured["options"], {"raw": "True"})

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

    def test_user_and_manager_permissions(self):
        printer = self.new_record()
        user = new_test_user(
            self.env,
            login="printer-user",
            groups="base.group_user",
        )
        manager = new_test_user(
            self.env,
            login="printer-manager",
            groups="base.group_erp_manager",
        )
        user_printer = printer.with_user(user)
        self.assertTrue(user_printer.has_access("read"))
        self.assertFalse(user_printer.has_access("create"))
        self.assertFalse(user_printer.has_access("write"))
        self.assertFalse(user_printer.has_access("unlink"))
        manager_printer = printer.with_user(manager)
        for operation in ("read", "create", "write", "unlink"):
            self.assertTrue(manager_printer.has_access(operation))
