# Copyright (C) 2019 IBM Corp.
# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class StockPikcing(TransactionCase):
    def setUp(self):
        super(StockPikcing, self).setUp()

        self.stock_location = self.env.ref("stock.stock_location_stock")
        self.customer_location = self.env.ref("stock.stock_location_customers")
        stock_location_locations_virtual = self.env["stock.location"].create(
            {"name": "Virtual Locations", "usage": "view", "posz": 1}
        )
        self.scrapped_location = self.env["stock.location"].create(
            {
                "name": "Scrapped",
                "location_id": stock_location_locations_virtual.id,
                "scrap_location": True,
                "usage": "inventory",
            }
        )

        uom_unit = self.env.ref("uom.product_uom_unit")

        self.product_A = self.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "list_price": 1.0,
                "categ_id": self.env.ref("product.product_category_all").id,
                "uom_id": uom_unit.id,
            }
        )

        self.country_us = self.env["res.country"].search(
            [("code", "like", "US")], limit=1
        )
        self.partner = self.env["res.partner"].create(
            {"name": "BOdedra", "country_id": self.country_us.id}
        )

        self.so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product_A.name,
                            "product_id": self.product_A.id,
                            "product_uom_qty": 2,
                            "product_uom": self.product_A.uom_id.id,
                            "price_unit": self.product_A.list_price,
                        },
                    )
                ],
                "pricelist_id": self.env.ref("product.list0").id,
                "picking_policy": "direct",
            }
        )

        self.uom_unit = self.env.ref("uom.product_uom_unit")

    def test_stock_picking_auto_print(self):
        """ Auto print when DO is ready or done
        """
        self.env["stock.quant"]._update_available_quantity(
            self.product_A, self.stock_location, 2
        )
        self.so.action_confirm()
        for picking in self.so.picking_ids:
            picking.move_lines._do_unreserve()

            # Unreserve picking and update default report configuration
            picking.move_lines._do_unreserve()

            # Made Delivery Slip report as a default report
            deliveryslip_report = self.env["ir.actions.report"].search(
                [("report_name", "=", "stock.report_deliveryslip")]
            )

            deliveryslip_report.write({"is_default_report": True})
            picking.action_assign()

            # Remove country ID from Delivery Slip report
            deliveryslip_report.write(
                {"country_id": self.country_us.id, "company_id": False}
            )
            picking.action_confirm()
            picking.action_assign()

            picking.move_lines._do_unreserve()

            # Unreserve picking and update default report configuration
            picking.do_unreserve()

            # Remove company ID from Delivery Slip report
            deliveryslip_report.write(
                {"company_id": self.env.user.company_id.id, "country_id": False}
            )
            picking.action_confirm()
            picking.action_assign()

            picking.do_unreserve()
            picking.move_lines._do_unreserve()

            deliveryslip_report.write(
                {
                    "company_id": self.env.user.company_id.id,
                    "country_id": self.country_us.id,
                }
            )
            picking.action_confirm()
            picking.action_assign()
            picking.action_done()
