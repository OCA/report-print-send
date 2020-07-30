# Copyright 2019 Compassion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PrinterOption(models.Model):
    _name = 'printer.option'
    _description = 'Printer Option'
    _rec_name = 'option_key'

    option_key = fields.Char(required=True, readonly=True)
    printer_id = fields.Many2one(
        comodel_name='printing.printer',
        string='Printer',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
