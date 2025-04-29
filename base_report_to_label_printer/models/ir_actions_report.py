# Copyright (C) 2022 Raumschmiede GmbH - Christopher Hansen (<https://www.raumschmiede.de>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    label = fields.Boolean(string="Report is a Label")

    def _get_user_default_print_behaviour(self):
        result = super()._get_user_default_print_behaviour()
        if self.label:
            user = self.env.user
            result["printer"] = user.default_label_printer_id or result["printer"]
        return result
