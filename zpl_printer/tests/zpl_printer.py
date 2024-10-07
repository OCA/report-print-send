from odoo.tests import common, tagged

DEFAULT_PRINTER_URL = "https://default_printer.my_company_network.internal"
OTHER_PRINTER_URL = "https://other_printer.my_company_network.internal"


class TestZplPrinterBase(common.TransactionCase):
    def setUp(self):
        super(TestZplPrinterBase, self).setUp()
        # if the database has a default printer, disable it for this test
        printer = self.env["zpl_printer.zpl_printer"].search([("default", "=", True)])
        if len(printer) >= 1:
            printer.default = False
        self.env["zpl_printer.zpl_printer"].create(
            [
                {
                    "name": "default",
                    "url": DEFAULT_PRINTER_URL,
                    "resolution": "200",
                    "default": True,
                },
                {
                    "name": "other_printer",
                    "url": OTHER_PRINTER_URL,
                    "resolution": "300",
                },
            ]
        )


@tagged("zpl")
class TestZplPrinter(TestZplPrinterBase):
    def test_write(self):
        """Changing the default flag of a printer should remove it from all other printers"""
        printer = self.env["zpl_printer.zpl_printer"].search(
            [("name", "=", "other_printer")]
        )
        printer.default = True
        default_after_change = self.env["zpl_printer.zpl_printer"].search(
            [("name", "=", "default")]
        )
        try:
            self.assertFalse(default_after_change.default)
        finally:
            default_after_change.default = True

    def test_get_label_printer_data(self):
        """Unless otherwise specified through this method, the default should be returned"""
        result = self.env["zpl_printer.zpl_printer"].get_label_printer_data(
            "unspecific_report_name", [1]
        )
        self.assertEqual(result, {"url": DEFAULT_PRINTER_URL, "resolution": "200"})
