# -*- coding: utf-8 -*-
# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class PrintingReportXmlAction(models.Model):
    _name = 'printing.report.xml.action'
    _description = 'Printing Report Printing Actions'

    report_id = fields.Many2one(comodel_name='ir.actions.report',
                                string='Report',
                                required=True,
                                ondelete='cascade')
    user_id = fields.Many2one(comodel_name='res.users',
                              string='User',
                              required=True,
                              ondelete='cascade')
    action = fields.Selection(
        selection=lambda s: s.env['printing.action']._available_action_types(),
        required=True,
    )
    printer_id = fields.Many2one(comodel_name='printing.printer',
                                 string='Printer')

    printer_tray_id = fields.Many2one(
        comodel_name='printing.tray',
        string='Paper Source',
        domain="[('printer_id', '=', printer_id)]",
    )

    @api.onchange('printer_id')
    def onchange_printer_id(self):
        """ Reset the tray when the printer is changed """
        self.printer_tray_id = False

    @api.multi
    def behaviour(self):
        if not self:
            return {}
        return {
            'action': self.action,
            'printer': self.printer_id,
            'tray': self.printer_tray_id.system_name
        }
