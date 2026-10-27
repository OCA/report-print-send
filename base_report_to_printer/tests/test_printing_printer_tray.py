# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import ReportToPrinterCommon


class TestPrintingPrinter(ReportToPrinterCommon):
    def setUp(self):
        super().setUp()
        self.Model = self.env["printing.printer"]
        self.printer = self.new_printer({"name": ""})
        self.tray_vals = {
            "name": "Tray",
            "system_name": "TrayName",
            "printer_id": self.printer.id,
        }

    def new_tray(self, tray_type="input", vals=None):
        values = self.tray_vals.copy()
        if vals:
            values.update(vals)
        return self.env["printing.tray." + tray_type].create(values)

    def test_tray_creation_and_link(self):
        """Debe crear una bandeja correctamente y vincularla a la impresora."""
        tray = self.new_tray()
        self.assertEqual(tray.printer_id, self.printer)
        self.assertEqual(tray.name, "Tray")
