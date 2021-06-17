# Copyright (c) 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from mock import patch

from odoo.tests.common import TransactionCase


class TestRemotePrinter(TransactionCase):
    def setUp(self):
        super().setUp()
        name = "testing_remote_server"
        self.remote = self.env["res.remote"].search([("name", "=", name)])
        if not self.remote:
            self.remote = self.env["res.remote"].create(
                {"name": name, "ip": "127.0.0.1"}
            )
        self.server = self.env["printing.server"].create(
            {"name": "Server", "address": "localhost", "port": 631}
        )
        self.printer_1 = self.env["printing.printer"].create(
            {"name": "Printer 1", "system_name": "P1", "server_id": self.server.id}
        )
        self.remote_printer = self.env["res.remote.printer"].create(
            {
                "remote_id": self.remote.id,
                "printer_id": self.printer_1.id,
                "is_default": True,
            }
        )
        self.Model = self.env["ir.actions.report"]
        self.report = self.env["ir.actions.report"].search([], limit=1)

    def test_behaviour_user_remote_values(self):
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "remote_default"
        with patch("odoo.addons.base_remote.models.base.Base.remote", new=self.remote):
            behaviour = report.behaviour()
        self.assertEqual(
            behaviour, {"action": "client", "printer": self.printer_1, "tray": False}
        )

    def test_behaviour_report_values(self):
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "client"
        report.property_printing_action_id = self.browse_ref(
            "remote_report_to_printer.printing_action_remote"
        )
        with patch("odoo.addons.base_remote.models.base.Base.remote", new=self.remote):
            behaviour = report.behaviour()
        self.assertDictEqual(
            behaviour, {"action": "server", "printer": self.printer_1, "tray": False}
        )

    def test_behaviour_user_action(self):
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "remote_default"
        report.property_printing_action_id = self.browse_ref(
            "remote_report_to_printer.printing_action_3"
        )
        with patch("odoo.addons.base_remote.models.base.Base.remote", new=self.remote):
            behaviour = report.behaviour()
        self.assertEqual(
            behaviour, {"action": "server", "printer": self.printer_1, "tray": False}
        )

    def test_behaviour_default_action(self):
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "client"
        with patch("odoo.addons.base_remote.models.base.Base.remote", new=self.remote):
            behaviour = report.behaviour()
        self.assertEqual(
            behaviour,
            {
                "action": "client",
                "printer": self.env["printing.printer"],
                "tray": False,
            },
        )

    def test_behaviour_no_printers(self):
        self.remote_printer.unlink()
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "remote_default"
        report.property_printing_action_id = self.browse_ref(
            "remote_report_to_printer.printing_action_3"
        )
        with patch("odoo.addons.base_remote.models.base.Base.remote", new=self.remote):
            behaviour = report.behaviour()
        self.assertEqual(behaviour["action"], "client")
