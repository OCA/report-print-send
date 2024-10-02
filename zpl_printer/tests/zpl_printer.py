from odoo.tests import common, tagged

_DEFAULT_PRINTER_URL = "https://default_printer.my_company_network.internal"


@tagged("zpl")
class TestZplPrinter(common.TransactionCase):
    def setUp(self):
        super(TestZplPrinter, self).setUp()
        self.env["zpl_printer.zpl_printer"].create(
            [
                {
                    "name": "default",
                    "url": _DEFAULT_PRINTER_URL,
                    "resolution": "200",
                    "default": True,
                },
                {
                    "name": "other_printer",
                    "url": "https://other_printer.my_company_network.internal",
                    "resolution": "300",
                },
            ]
        )

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
        self.assertEqual(result, {"url": _DEFAULT_PRINTER_URL, "resolution": "200"})
