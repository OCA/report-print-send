# Copyright (C) 2022 Raumschmiede GmbH - Christopher Hansen (<https://www.raumschmiede.de>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestIrActionsReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.Model = cls.env["ir.actions.report"].with_context(
            skip_printer_exception=True
        )
        cls.server = cls.env["printing.server"].create({})

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

    def test_print_behavior_user_label_printer(self):
        """It should return the label printer from user"""
        report = self.Model.search([], limit=1)
        report.label = True
        self.env.user.printing_action = "client"
        self.env.user.default_label_printer_id = self.new_printer()
        self.assertEqual(
            report.behaviour(),
            {
                "action": "client",
                "printer": self.env.user.default_label_printer_id,
                "tray": False,
            },
        )
