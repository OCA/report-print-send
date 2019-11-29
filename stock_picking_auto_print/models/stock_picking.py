# Copyright (C) 2019 IBM Corp.
# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def _stock_picking_default_auto_print_report(self):
        user_company_id = self.env.user.company_id.id
        report_action_pool = self.env['ir.actions.report']
        for picking in self.filtered(lambda p: p.sale_id):
            default_report_id = False

            # Find picking defaults reports
            default_report_ids = report_action_pool.search(
                [('model', '=', 'stock.picking'),
                 ('is_default_report', '=', True)]).ids

            # Check Partner country id
            country_id = False
            if picking.partner_id.country_id:
                country_id = picking.partner_id.country_id.id

            if default_report_ids and country_id:
                # Filter report with Country and Company
                report_ids = report_action_pool.search(
                    [('country_id', '=', country_id),
                     ('company_id', '=', user_company_id),
                     ('id', 'in', default_report_ids)],
                    limit=1)
                if report_ids:
                    default_report_id = report_ids.id

            if not default_report_id and country_id:
                # Filter report with Country
                report_ids = report_action_pool.search(
                    [('country_id', '=', country_id),
                     ('id', 'in', default_report_ids)],
                    limit=1)
                if report_ids:
                    default_report_id = report_ids.id

            if not default_report_id:
                # Filter report with Company
                report_ids = report_action_pool.search(
                    [('company_id', '=', user_company_id),
                     ('id', 'in', default_report_ids)],
                    limit=1)
                if report_ids:
                    default_report_id = report_ids.id

            if not default_report_id:
                default_report_id = self.env.ref(
                    'stock.action_report_picking').with_context(
                    landscape=True).report_action(picking).get('id')
            action_report = report_action_pool.browse(
                default_report_id)

            try:
                action_report.print_document(picking.id)
            except:
                pass
        return True

    @api.multi
    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if 'date_done' in vals:
            self._stock_picking_default_auto_print_report()
        return res

    @api.multi
    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        for picking in self:
            if (picking.picking_type_code == 'outgoing' or
                    picking.location_dest_id.name == 'Output') and \
                    picking.state == 'assigned':
                picking._stock_picking_default_auto_print_report()
        return res
