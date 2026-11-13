# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tools import mute_logger

from .common import PrinterZpl2Common, model


class TestWizardPrintTest(PrinterZpl2Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The label prints printing.printer records: the most recent one
        cls.other_printer = cls.printer.copy(
            {"name": "Other printer", "default": False}
        )
        cls.env["printing.label.zpl2.component"].create(
            {"name": "Name", "label_id": cls.label.id, "data": "object.name"}
        )

    def _open_wizard(self):
        action = self.label.action_print_test()
        self.assertEqual(action["res_model"], "wizard.zpl2.print_test")
        return (
            self.env[action["res_model"]].with_context(**action["context"]).create({})
        )

    def test_defaults(self):
        """The wizard is opened from the label, on its most recent record and
        the default printer"""
        wizard = self._open_wizard()
        self.assertEqual(wizard.label_id, self.label)
        self.assertEqual(wizard.model_id, self.label.model_id)
        self.assertEqual(wizard.record_ref, self.other_printer)
        self.assertEqual(wizard.printer_id, self.printer)

    @mute_logger("odoo.addons.base_report_to_printer.models.printing_printer")
    @patch(model + ".cups")
    def test_print(self, cups):
        """The label is printed for the selected record on the selected printer"""
        wizard = self._open_wizard()
        wizard.record_ref = self.printer
        wizard.action_print()
        cups.Connection().printFile.assert_called_once()

    def test_print_extra(self):
        """The extra arguments of the label are proposed, and can be changed
        for the test"""
        self.label.extra = "{'page_count': 2}"
        wizard = self._open_wizard()
        self.assertEqual(wizard.extra, "{'page_count': 2}")
        with patch.object(type(self.label), "print_label") as print_label:
            wizard.action_print()
        print_label.assert_called_once_with(
            self.printer, self.other_printer, page_count=2
        )
        wizard.extra = "{'page_count': 3}"
        with patch.object(type(self.label), "print_label") as print_label:
            wizard.action_print()
        print_label.assert_called_once_with(
            self.printer, self.other_printer, page_count=3
        )
        self.assertEqual(self.label.extra, "{'page_count': 2}")

    def test_print_wrong_model(self):
        """A record of another model is refused"""
        wizard = self._open_wizard()
        wizard.record_ref = self.env.user
        with self.assertRaises(UserError):
            wizard.action_print()
