# Copyright (c) 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def _get_user_default_print_behaviour(self):
        res = super()._get_user_default_print_behaviour()
        if res.get('action', 'unknown') == 'remote_default':
            res.update(self.remote.get_printer_behaviour())
        return res

    @api.multi
    def _get_report_default_print_behaviour(self):
        res = super()._get_report_default_print_behaviour()
        if res.get('action', 'unknown') == 'remote_default':
            res.update(self.remote.get_printer_behaviour())
        return res
