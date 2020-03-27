# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PrintingReportXmlAction(models.Model):
    _name = 'printing.report.xml.action'
    _description = 'Printing Report Printing Actions'

    report_id = fields.Many2one(comodel_name='ir.actions.report',
                                string='Report',
                                required=True,
                                ondelete='cascade')
    user_id = fields.Many2one(comodel_name='res.users',
                              string='User',
                              ondelete='cascade')
    language_id = fields.Many2one('res.lang', 'Language')
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

    _sql_constraints = [(
        'unique_configuration', 'unique(report_id,user_id,language_id)',
        'There is already an action defined for this user/language.'
    )]

    @api.constrains('user_id', 'language_id')
    def check_action(self):
        for action in self:
            if not action.user_id and not action.language_id:
                raise UserError(_(
                    "You should set a user or a language for which this action "
                    "applies to."))

    @api.onchange('printer_id')
    def onchange_printer_id(self):
        """ Reset the tray when the printer is changed """
        self.printer_tray_id = False

    @api.multi
    def behaviour(self):
        action = self
        if len(action) > 1:
            action = self.select_action()
        if not action:
            return {}
        return {
            'action': action.action,
            'printer': action.printer_id,
            'tray': action.printer_tray_id.system_name
        }

    @api.multi
    def select_action(self):
        """
        Returns the action that makes the most sense for the print depending
        on the context (user and language).
        :return: One record of printing.report.xml.action
        """
        action = self
        if len(self) > 1:
            # Find the most relevant action : user first, language second
            user_action = self.filtered(lambda a: a.user_id == self.env.user)
            if user_action:
                if len(user_action) == 1:
                    action = user_action
                else:
                    user_language_action = user_action.filtered(
                        lambda a: a.language_id.code == self.env.lang)
                    if user_language_action:
                        action = user_language_action
            else:
                action = self.filtered(lambda a: a.language_id.code == self.env.lang)
        return action
