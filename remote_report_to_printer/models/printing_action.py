# Copyright (c) 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PrintingAction(models.Model):
    _inherit = 'printing.action'

    @api.model
    def _available_action_types(self):
        res = super()._available_action_types()
        res.append(('remote_default', "Use remote's default"))
        return res

    action_type = fields.Selection(
        selection=_available_action_types,
    )
