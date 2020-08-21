from odoo import models, fields


class BrowserPrintLabel(models.TransientModel):
    _name = 'wizard.browser.print.label'
    _description = 'Browser Print Label'

    label_id = fields.Many2one(
        comodel_name='printing.label.zpl2', string='Label', required=True,
        domain=lambda self: [
            ('model_id.model', '=', self.env.context.get('active_model'))],
        help='Label to print.')
