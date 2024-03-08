# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestPrintingReportXmlAction(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Model = self.env["printing.report.xml.action"]

        self.report = self.env["ir.actions.report"].search([], limit=1)
        self.server = self.env["printing.server"].create({})

        self.report_vals = {
            "report_id": self.report.id,
            "user_id": self.env.ref("base.user_demo").id,
            "action": "server",
        }

    def new_record(self, vals=None):
        values = self.report_vals
        if vals is not None:
            values.update(vals)

        return self.Model.create(values)

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

    def test_behaviour(self):
        """It should return some action's data, unless called on empty
        recordset
        """
        xml_action = self.new_record()
        self.assertEqual(
            xml_action.behaviour(),
            {
                "action": xml_action.action,
                "printer": xml_action.printer_id,
                "tray": False,
            },
        )

        xml_action = self.new_record({"printer_id": self.new_printer().id})
        self.assertEqual(
            xml_action.behaviour(),
            {
                "action": xml_action.action,
                "printer": xml_action.printer_id,
                "tray": False,
            },
        )

        self.assertEqual(self.Model.behaviour(), {})

    def test_onchange_printer_tray_id_empty(self):
        action = self.env["printing.report.xml.action"].new({"printer_tray_id": False})
        action.onchange_printer_id()
        self.assertFalse(action.printer_tray_id)

    def test_onchange_printer_tray_id_not_empty(self):
        server = self.env["printing.server"].create({})
        printer = self.env["printing.printer"].create(
            {
                "name": "Printer",
                "server_id": server.id,
                "system_name": "Sys Name",
                "default": True,
                "status": "unknown",
                "status_message": "Msg",
                "model": "res.users",
                "location": "Location",
                "uri": "URI",
            }
        )
        tray = self.env["printing.tray"].create(
            {"name": "Tray", "system_name": "TrayName", "printer_id": printer.id}
        )

        action = self.env["printing.report.xml.action"].new(
            {"printer_tray_id": tray.id}
        )
        self.assertEqual(action.printer_tray_id, tray)
        action.onchange_printer_id()
        self.assertFalse(action.printer_tray_id)
