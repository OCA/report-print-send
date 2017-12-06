from odoo import models, fields, api, _
from odoo.addons.queue_job.job import job
from odoo import exceptions


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    automated_action_ids = fields.One2many(
        comodel_name='base.automation',
        inverse_name='report_id',
        string='Automated Printing Actions',
    )

    @api.depends('model')
    def _compute_model_id(self):
        Model = self.env['ir.model']
        for report in self:
            report.model_id = Model._get(report.model)

    model_id = fields.Many2one(
        comodel_name='ir.model',
        compute='_compute_model_id',
        store=True,
    )

    @job
    @api.multi
    def print_document_auto(self, record_ids, behaviour=None, data=None):
        behaviour = behaviour or self.behaviour()
        document, doc_format = self.with_context(
            must_skip_send_to_printer=True,
            behaviour=behaviour).render_qweb_pdf(
                record_ids, data=data)
        printer = behaviour.pop('printer')
        if not printer:
            raise exceptions.Warning(
                _('No printer configured to print this report.')
            )
        return printer.print_document(self, document,
                                      doc_format=self.report_type,
                                      **behaviour)

    @api.multi
    def behaviour(self):
        if self._context.get('behaviour'):
            return {self: self._context['behaviour']}
        return super(IrActionsReport, self).behaviour()
