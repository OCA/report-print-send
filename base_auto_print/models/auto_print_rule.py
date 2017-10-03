from odoo import models, fields, api
from odoo.addons.queue_job.job import job


class Report(models.Model):
    _inherit = 'report'

    @job
    @api.model
    def _print_document_automatically(self, report_name, records, filters):
        Report = self.env['report']
        report = Report._get_report_from_name(report_name)
        PrintRule = self.env['auto.print.rule'].sudo()
        for record in records:
            search_args = [('action_id', '=', report.id)]
            for field in filters:
                if field in record._fields:
                    search_args.append(
                        getattr(PrintRule, '_handle_field_%s' % field,
                                PrintRule._field_handle_default)(record, field))
            rule = PrintRule.search(search_args)
            # or should we fail here, what if user has no rule
            sudo_uid = rule[0].user_id.id if rule else self.env.uid
            Report.sudo(sudo_uid).print_document([record.id], report_name)
        return True

    @api.model
    def print_document_automatically(self, report_name, records, filters,
                                     delay=True):
        if delay:
            self.with_delay()._print_document_automatically(
                report_name, records, filters)
        else:
            self._print_document_automatically(report_name, records, filters)


class IrActionsReportXml(models.Model):

    _inherit = 'ir.actions.report.xml'

    auto_print_rule_ids = fields.One2many(
        comodel_name='auto.print.rule',
        inverse_name='action_id',
        string='Automated Print Rules',
    )


class AutomatedPrintCriteria(models.Model):
    _name = 'auto.print.rule'

    action_id = fields.Many2one(
        comodel_name='ir.actions.report.xml', required=True)
    user_id = fields.Many2one(comodel_name='res.users', string='Print as User')
    product = fields.Many2many(
        comodel_name='product.product', string='Products')
    company = fields.Many2many(comodel_name='res.company', string='Companies')
    warehouse = fields.Many2many(
        comodel_name='stock.warehouse', string='Warehouses')
    product_category = fields.Many2many(
        comodel_name='product.category', string='Product Categories')

    @api.model
    def _field_handle_default(self, record, field):
        self.ensure_one()
        return field, 'in', record[field].ids()

    @api.model
    def _field_handle_product_category(self, record, field):
        self.ensure_one()
        return ('product_id.product_categ_id', 'in',
                record.product_id.product_categ_id.ids())
