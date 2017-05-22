# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PrintingReportXMLAction(models.Model):
    _inherit = 'printing.report.xml.action'

    copies = fields.Integer(
        string='Copies',
        default=1
    )

    @api.multi
    def behaviour(self):
        self.ensure_one()
        res = super(PrintingReportXMLAction, self).behaviour()
        res['copies'] = self.copies
        return res
