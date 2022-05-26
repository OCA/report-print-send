# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase

model = "odoo.addons.base_report_to_printer.models.printing_server"


class TestPrintingTray(TransactionCase):
    def setUp(self):
        super(TestPrintingTray, self).setUp()
        self.Model = self.env["printing.tray"]
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
        self.tray_vals = {
            "name": "Tray",
            "system_name": "TrayName",
            "printer_id": self.printer.id,
        }

    def new_tray(self):
        return self.env["printing.tray"].create(self.tray_vals)

    def test_report_behaviour(self):
        """It should add the selected tray in the report data"""
        ir_report = self.env["ir.actions.report"].search([], limit=1)
        report = self.env["printing.report.xml.action"].create(
            {"user_id": self.env.user.id, "report_id": ir_report.id, "action": "server"}
        )
        report.printer_tray_id = False
        behaviour = report.behaviour()
        self.assertEqual(behaviour["tray"], False)

        # Check that we have te right value
        report.printer_tray_id = self.new_tray()
        behaviour = report.behaviour()
        self.assertEqual(behaviour["tray"], report.printer_tray_id.system_name)
