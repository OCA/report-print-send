from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    state = fields.Selection(selection_add=[('print', 'Print a Report')])
    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        domain="[('model_id', '=', model_id)]",
        ondelete='set null',
    )
    printer_id = fields.Many2one(
        comodel_name='printing.printer',
        string='Printer',
    )
    printer_tray_id = fields.Many2one(
        comodel_name='printing.tray',
        string='Paper Source',
        domain="[('printer_id', '=', printer_id)]",
    )

    print_action_type = fields.Selection(
        [('server', 'Use Automated Action Printer'),
         ('report', 'Use Rules defined on Report')],
    )

    print_options = fields.Char(
        help='A dictionary of print options to pass to the report.  '
             'Requires knowledge of CUPS PPD\'s and specific capabilities of '
             'printers but allows setting for example: \n'
             '  - Duplex\n'
             '  - Billing Codes\n'
             '  - Media Types\n'
             '  - PIN Printing\n '
             'Should look like {\'Duplex\': \'DuplexNoTumble\', '
             '\'OutputBin\': \'UpperLeftBin\'}',
    )

    @api.model
    def run_action_print(self, action, eval_context=None):
        if not action.report_id:
            return False
        description = 'Print %s' % action.report_id.name
        if eval_context.get('records'):
            record_ids = eval_context['records'].ids
            description = description + ' for ' + ','.join(
                [x[1] for x in eval_context['records'].name_get()])
        else:
            record_ids = None
        action.report_id.with_delay(description=description)\
            .print_document_auto(record_ids, behaviour=self.print_behaviour())
        return False

    @api.multi
    def print_behaviour(self):
        self.ensure_one()
        if self.print_action_type == 'report':
            return {}
        return dict(action=self.print_action_type,
                    printer=self.printer_id,
                    tray=self.printer_tray_id.system_name,
                    **safe_eval(self.print_options)
                    )

    @api.constrains('print_options')
    def constraint_print_options(self):
        for record in self.filtered(lambda r: r.print_action_type == 'server'):

            if not isinstance(safe_eval(record.print_options), dict):
                raise ValidationError('Print options must be an evaluable '
                                      'dictionary')

    @api.onchange('state')
    def change_print_state(self):
        if self.state != 'print':
            self.printer_id = False
            self.report_id = False
            self.printer_tray_id = False
            self.print_options = False
            self.print_action_type = False
        else:
            self.print_action_type = 'server'
            self.print_options = '{}'
