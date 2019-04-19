# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields


class PrintRecordLabel(models.TransientModel):
    _name = 'wizard.print.record.label'
    _description = 'Print Record Label'

    printer_id = fields.Many2one(
        comodel_name='printing.printer', string='Printer', required=True,
        help='Printer used to print the labels.')
    label_id = fields.Many2one(
        comodel_name='printing.label.zpl2', string='Label', required=True,
        domain=lambda self: [
            ('model_id.model', '=', self.env.context.get('active_model'))],
        help='Label to print.')

    @api.model
    def default_get(self, fields_list):
        values = super(PrintRecordLabel, self).default_get(fields_list)

        # Automatically select the printer and label, if only one is available
        printers = self.env['printing.printer'].search(
            [('id', '=', self.env.context.get('printer_zpl2_id'))])
        if not printers:
            printers = self.env['printing.printer'].search([])
        if len(printers) == 1:
            values['printer_id'] = printers.id

        labels = self.env['printing.label.zpl2'].search([
            ('model_id.model', '=', self.env.context.get('active_model')),
        ])
        if len(labels) == 1:
            values['label_id'] = labels.id

        return values

    def print_label(self):
        """ Prints a label per selected record """
        record_model = self.env.context['active_model']
        for record_id in self.env.context['active_ids']:
            record = self.env[record_model].browse(record_id)
            self.label_id.print_label(self.printer_id, record)
