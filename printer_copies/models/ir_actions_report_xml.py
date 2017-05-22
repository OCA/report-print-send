# -*- coding: utf-8 -*-

from odoo import fields, models


class IrActionsReportXml(models.Model):
    _inherit = 'ir.actions.report.xml'

    copies = fields.Integer(
        string='Copies',
        default=1
    )
