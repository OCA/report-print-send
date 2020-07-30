# Copyright 2019 Compassion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PrinterOptionChoice(models.Model):
    _name = 'printer.option.choice'
    _description = 'Printer Option Choice'
    _rec_name = 'composite_key'

    option_key = fields.Char(required=True, readonly=True)
    option_value = fields.Char(required=True, readonly=True)
    composite_key = fields.Char(compute='_compute_composite_key', store=True)
    printer_id = fields.Many2one(
        comodel_name='printing.printer',
        string='Printer',
        required=True,
        readonly=True,
        ondelete='cascade',
    )

    @api.multi
    @api.depends("option_key", "option_value")
    def _compute_composite_key(self):
        """ Composite key for a printing option key-value pair."""
        for option in self:
            option.composite_key = self.build_composite_key(option.option_key,
                                                            option.option_value
                                                            )

    @api.model
    def build_composite_key(self, option_key, option_value):
        return option_key + ':' + option_value
