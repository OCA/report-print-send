# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PrintingReportXMLAction(models.Model):
    _inherit = 'printing.report.xml.action'

    printer_input_tray_id = fields.Many2one(
        comodel_name='printing.tray.input',
        string='Paper Source',
        domain="[('printer_id', '=', printer_id)]",
        oldname="printer_tray_id"
    )
    printer_output_tray_id = fields.Many2one(
        comodel_name='printing.tray.output',
        string='Output Bin',
        domain="[('printer_id', '=', printer_id)]",
    )

    @api.multi
    def behaviour(self):
        self.ensure_one()
        res = super(PrintingReportXMLAction, self).behaviour()
        res['input_tray'] = self.printer_input_tray_id.system_name
        res['output_tray'] = self.printer_output_tray_id.system_name
        return res

    @api.onchange('printer_id')
    def onchange_printer_id(self):
        """ Reset the tray when the printer is changed """
        self.printer_input_tray_id = False
        self.printer_output_tray_id = False
