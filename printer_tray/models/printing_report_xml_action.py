# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PrintingReportXMLAction(models.Model):
    _inherit = 'printing.report.xml.action'

    printer_tray_id = fields.Many2one(
        comodel_name='printing.tray',
        string='Paper Source',
        domain="[('printer_id', '=', printer_id)]",
    )

    @api.multi
    def behaviour(self):
        self.ensure_one()
        res = super(PrintingReportXMLAction, self).behaviour()
        res['tray'] = self.printer_tray_id.system_name
        return res

    @api.onchange('printer_id')
    def onchange_printer_id(self):
        """ Reset the tray when the printer is changed """
        self.printer_tray_id = False
