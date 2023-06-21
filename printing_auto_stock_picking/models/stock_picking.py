# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "printing.auto.mixin"]

    auto_printing_ids = fields.Many2many(
        "printing.auto", related="picking_type_id.auto_printing_ids"
    )

    def _action_done(self):
        result = super()._action_done()
        self.handle_print_auto()
        return result
