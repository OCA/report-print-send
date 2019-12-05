# Copyright 2019 Compassion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class IrActionsReportXml(models.Model):
    _inherit = 'ir.actions.report'

    printer_options = fields.Many2many('printer.option.choice',
                                       string='Printer Options')

    @api.multi
    @api.onchange('printing_printer_id')
    def on_change_printer(self):
        for report in self:
            report.printer_options = False
