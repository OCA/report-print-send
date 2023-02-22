# Copyright (C) 2018 Florent de Labarre (<https://github.com/fmdl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase

model = "odoo.addons.base_report_to_printer.models.printing_server"


class TestWizardPrintRecordLabel(TransactionCase):
    def setUp(self):
        super(TestWizardPrintRecordLabel, self).setUp()
        self.Model = self.env["wizard.print.record.label"]
        self.server = self.env["printing.server"].create({})
        self.printer = self.env["printing.printer"].create(
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
        self.label = self.env["printing.label.zpl2"].create(
            {
                "name": "ZPL II Label",
                "model_id": self.env.ref(
                    "base_report_to_printer.model_printing_printer"
                ).id,
            }
        )

    def test_create_action(self):
        """Check the creation of action"""
        self.label.create_action()
        self.assertTrue(self.label.action_window_id)

    def test_unlink_action(self):
        """Check the unlink of action"""
        self.label.unlink_action()
        self.assertFalse(self.label.action_window_id)
