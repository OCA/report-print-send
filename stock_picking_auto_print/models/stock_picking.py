# Copyright (C) 2019 IBM Corp.
# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _search_default_report(self, country_id=False, company_id=False):
        report_id = False
        report_action_pool = self.env["ir.actions.report"]
        domain = [("model", "=", "stock.picking"), ("is_default_report", "=", True)]
        fields = ["country_id", "company_id"]
        stock_picking_reports = report_action_pool.search_read(domain, fields)
        if country_id and company_id:
            for value in stock_picking_reports:
                if value.get("country_id") and value.get("company_id"):
                    if (
                        value.get("country_id")[0] == country_id
                        and value.get("company_id")[0] == company_id
                    ):
                        return value["id"]
        elif country_id:
            for value in stock_picking_reports:
                if value.get("country_id"):
                    if value.get("country_id")[0] == country_id:
                        return value["id"]
        elif company_id:
            for value in stock_picking_reports:
                if value.get("company_id"):
                    if value.get("company_id")[0] == company_id:
                        return value["id"]
        else:
            report_id = (
                self.env.ref("stock.action_report_picking")
                .with_context(landscape=True)
                .report_action(self)
                .get("id")
            )
        return report_id

    def _stock_picking_default_auto_print_report(self):
        user_company_id = self.env.user.company_id.id
        report_action_pool = self.env["ir.actions.report"]
        for picking in self.filtered(lambda p: p.sale_id):
            default_report_id = False
            # Check Partner country id
            country_id = False
            if picking.partner_id.country_id:
                country_id = picking.partner_id.country_id.id

            if country_id and user_company_id:
                # Filter report with Country and Company
                default_report_id = picking._search_default_report(
                    country_id, user_company_id
                )

            if not default_report_id and country_id:
                # Filter report with Country
                default_report_id = picking._search_default_report(
                    country_id=country_id
                )

            if not default_report_id:
                # Filter report with Company
                default_report_id = picking._search_default_report(
                    company_id=user_company_id
                )

            if not default_report_id:
                # Search for default picking operation report
                default_report_id = picking._search_default_report()

            action_report = report_action_pool.browse(default_report_id)

            try:
                action_report.print_document(picking.id)
            except Exception:
                pass
        return True

    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if "date_done" in vals:
            self._stock_picking_default_auto_print_report()
        return res

    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        for picking in self:
            if (
                picking.picking_type_code == "outgoing"
                or picking.location_dest_id.name == "Output"
            ) and picking.state == "assigned":
                picking._stock_picking_default_auto_print_report()
        return res
