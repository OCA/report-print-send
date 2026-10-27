# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import ReportToPrinterCommon

model = "odoo.addons.base_report_to_printer.models.printing_server"


class TestPrintingTray(ReportToPrinterCommon):
    def setUp(self):
        super().setUp()
        self.printer = self.new_printer()
        self.tray_vals = {
            "name": "Tray",
            "system_name": "TrayName",
            "printer_id": self.printer.id,
        }

    def new_tray(self, tray_type="input"):
        return self.env["printing.tray." + tray_type].create(self.tray_vals)

    def test_report_behaviour(self):
        """It should add the selected tray in the report data"""
        ir_report = self.env["ir.actions.report"].search([], limit=1)
        report = self.env["printing.report.xml.action"].create(
            {
                "user_id": self.env.user.id,
                "report_id": ir_report.id,
                "action": "server",
            }
        )
        report.printer_input_tray_id = False
        report.printer_output_tray_id = False
        behaviour = report.behaviour()
        self.assertEqual(behaviour["input_tray"], False)
        self.assertEqual(behaviour["output_tray"], False)

        # Check that we have te right value
        report.printer_input_tray_id = self.new_tray()
        report.printer_output_tray_id = self.new_tray("output")
        behaviour = report.behaviour()
        self.assertEqual(
            behaviour["input_tray"], report.printer_input_tray_id.system_name
        )
        self.assertEqual(
            behaviour["output_tray"], report.printer_output_tray_id.system_name
        )
