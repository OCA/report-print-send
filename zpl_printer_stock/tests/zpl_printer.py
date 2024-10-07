from odoo.tests import tagged

from odoo.addons.zpl_printer.tests.zpl_printer import (
    DEFAULT_PRINTER_URL,
    OTHER_PRINTER_URL,
    TestZplPrinterBase,
)


@tagged("zpl")
class TestZplPrinterStock(TestZplPrinterBase):
    _unspecific_lot_id = 0
    _other_printer_lot_id = 0

    def setUp(self):
        super(TestZplPrinterStock, self).setUp()
        second_printer = self.env["zpl_printer.zpl_printer"].search(
            [("name", "=", "other_printer")]
        )
        (unspecific_product, other_printer_product) = self.env[
            "product.product"
        ].create(
            [
                {
                    "name": "Unspecific Product",
                    "type": "product",
                    "tracking": "serial",
                },
                {
                    "name": "Product with different printer",
                    "type": "product",
                    "tracking": "serial",
                },
            ]
        )
        other_printer_product.product_tmpl_id.zpl_printer_id = second_printer
        lots = self.env["stock.lot"].create(
            [
                {
                    "name": "UP-00001",
                    "product_id": unspecific_product.id,
                },
                {
                    "name": "OPP-00001",
                    "product_id": other_printer_product.id,
                },
            ]
        )
        self._unspecific_lot_id = lots[0].id
        self._other_printer_lot_id = lots[1].id

    def test_get_label_printer_data_for_anything(self):
        """Unless otherwise specified through this method, the default should be returned"""
        result = self.env["zpl_printer.zpl_printer"].get_label_printer_data(
            "stock.label_lot_template_view", [self._unspecific_lot_id]
        )
        self.assertEqual(result, {"url": DEFAULT_PRINTER_URL, "resolution": "200"})

    def test_get_label_printer_data_for_product_with_other_printer(self):
        """Unless otherwise specified through this method, the default should be returned"""
        result = self.env["zpl_printer.zpl_printer"].get_label_printer_data(
            "stock.label_lot_template_view", [self._other_printer_lot_id]
        )
        self.assertEqual(result, {"url": OTHER_PRINTER_URL, "resolution": "300"})
