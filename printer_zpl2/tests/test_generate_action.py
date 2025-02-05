# Copyright (C) 2018 Florent de Labarre (<https://github.com/fmdl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import PrinterZpl2Common

model = "odoo.addons.base_report_to_printer.models.printing_server"


class TestWizardPrintRecordLabel(PrinterZpl2Common):
    def test_create_action(self):
        """Check the creation of action"""
        self.label.create_action()
        self.assertTrue(self.label.action_window_id)

    def test_unlink_action(self):
        """Check the unlink of action"""
        self.label.unlink_action()
        self.assertFalse(self.label.action_window_id)
