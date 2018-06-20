# Copyright (c) 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResRemote(models.Model):
    _inherit = 'res.remote'

    remote_printer_ids = fields.One2many(
        'res.remote.printer',
        inverse_name='remote_id',
    )

    @api.multi
    def get_printer_behaviour(self):
        self.ensure_one()
        printer_usage = self.env.context.get('printer_usage', 'standard')
        printers = self.remote.remote_printer_ids.filtered(
            lambda r: r.printer_usage == printer_usage
        ).sorted(key='is_default', reverse=True)
        if printers:
            printer = printers[0]
            return {
                'action': 'server',
                'printer': printer.printer_id,
                'tray': printer.printer_tray_id.system_name
            }
        return {'action': 'client'}
