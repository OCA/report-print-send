# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions, fields, models, _
from odoo.tools.safe_eval import safe_eval


class PrintingLabelZpl2(models.Model):
    _inherit = 'printing.label.zpl2'
    _description = 'ZPL II Label'
    _order = 'model_id, name, id'

    action_window_id = fields.Many2one(
        comodel_name='ir.actions.act_window', string='Action', readonly=True)
    test_print_mode = fields.Boolean(string='Mode Print')
    printer_id = fields.Many2one(
        comodel_name='printing.printer', string='Printer')

    def print_label(self, printer, record, page_count=1, **extra):
        for label in self:
            if record._name != label.model_id.model:
                raise exceptions.UserError(
                    _('This label cannot be used on {model}').format(
                        model=record._name))

            # Send the label to printer
            label_contents = label._generate_zpl2_data(
                record, page_count=page_count, **extra)
            printer.print_document(
                report=None, content=label_contents, doc_format='raw')

        return True

    def create_action(self):
        for label in self.filtered(lambda record: not record.action_window_id):
            vals = {
                'name': _('Print Label'),
                'src_model': label.model_id.model,
                'binding_model_id': label.model_id.id,
                'res_model': 'wizard.print.record.label',
                'view_mode': 'form',
                'target': 'new',
                'binding_type': 'action',
            }
            # Provide a valid xml_id for the record, so that in case we
            # uninstall the module, these records will also be deleted.
            # Otherwise an error would occur indicating that model
            # 'wizard.print.record.label' as the action is not going to be
            # deleted when you uninstall the module.
            xml_id = 'printer_zpl2.%s' % label.id
            label.action_window_id = self.env['ir.model.data']._update(
                'ir.actions.act_window', 'printer_zpl2', vals, xml_id)
        return True

    def unlink_action(self):
        self.mapped('action_window_id').unlink()

    def print_test_label(self):
        for label in self:
            if label.test_print_mode and label.record_id and label.printer_id:
                record = label._get_record()
                extra = safe_eval(label.extra, {'env': self.env})
                if record:
                    label.print_label(label.printer_id, record, **extra)
