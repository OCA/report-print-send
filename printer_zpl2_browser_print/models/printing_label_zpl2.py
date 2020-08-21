from odoo import models, _, fields


class PrintingLabelZpl2(models.Model):
    _inherit = 'printing.label.zpl2'
    browser_print_action_window_id = fields.Many2one(
        comodel_name='ir.actions.act_window', string='Browser Print Action',
        readonly=True)

    def create_browser_print_action(self):
        for label in self.filtered(
            lambda record: not record.browser_print_action_window_id
        ):
            label.browser_print_action_window_id = self.env[
                'ir.actions.act_window'
            ].create({
                'name': _('Browser Print Label'),
                'src_model': label.model_id.model,
                'binding_model_id': label.model_id.id,
                'res_model': 'wizard.browser.print.label',
                'view_mode': 'form',
                'target': 'new',
                'binding_type': 'action',
            })
        return True

    def unlink_browser_print_action(self):
        self.mapped('browser_print_action_window_id').unlink()

    def browser_print_label(self):
        self.ensure_one()
        records = self.env[self.env.context['active_model']].browse(
            self.env.context['active_ids'])
        res = []
        for record in records:
            res.append(self._generate_zpl2_data(record))
        return res
