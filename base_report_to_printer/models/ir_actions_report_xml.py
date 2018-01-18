# -*- coding: utf-8 -*-
# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# Copyright (C) 2018 KMEE INFORMATICA LTDA (<http://kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, tools


class IrActionsReportXml(models.Model):
    """
    Reports
    """

    _inherit = 'ir.actions.report.xml'

    property_printing_action_id = fields.Many2one(
        comodel_name='printing.action',
        string='Action',
        company_dependent=True,
    )
    printing_printer_id = fields.Many2one(
        comodel_name='printing.printer',
        string='Printer'
    )
    printing_action_ids = fields.One2many(
        comodel_name='printing.report.xml.action',
        inverse_name='report_id',
        string='Actions',
        help='This field allows configuring action and printer on a per '
             'user basis'
    )

    @api.model
    def print_action_for_report_name(self, report_name):
        """ Returns if the action is a direct print or pdf

        Called from js
        """
        report = self.search([('report_name', '=', report_name)], limit=1)
        if not report:
            return {}
        result = report.behaviour()[report.id]
        serializable_result = {
            'action': result['action'],
            'printer_name': result['printer'].name,
        }
        return serializable_result

    @api.multi
    def behaviour(self):
        result = {}
        printer_obj = self.env['printing.printer']
        printing_act_obj = self.env['printing.report.xml.action']
        # Set hardcoded default action
        default_action = 'client'
        # Retrieve system wide printer
        default_printer = printer_obj.get_default()

        # Retrieve user default values
        user = self.env.user
        if user.printing_action:
            default_action = user.printing_action
        if user.printing_printer_id:
            default_printer = user.printing_printer_id

        for report in self:
            action = default_action
            printer = default_printer

            # Retrieve report default values
            report_action = report.property_printing_action_id
            if report_action and report_action.action_type != 'user_default':
                action = report_action.action_type
            if report.printing_printer_id:
                printer = report.printing_printer_id

            # Retrieve report-user specific values
            print_action = printing_act_obj.search(
                [('report_id', '=', report.id),
                 ('user_id', '=', self.env.uid),
                 ('action', '!=', 'user_default')],
                limit=1)
            if print_action:
                user_action = print_action.behaviour()
                action = user_action['action']
                if user_action['printer']:
                    printer = user_action['printer']

            result[report.id] = {'action': action,
                                 'printer': printer,
                                 }
        return result

    @api.multi
    def _can_print_report(self, behaviour, printer, document):
        """Predicate that decide if report can be sent to printer

        If you want to prevent `get_pdf` to send report you can set
        the `must_skip_send_to_printer` key to True in the context
        """
        if self.env.context.get('must_skip_send_to_printer'):
            return False
        if behaviour['action'] == 'server' and printer and document:
            return True
        return False

    @api.model
    def render_report(self, res_ids, name, data):
        """
        Look up a report definition and render the report for the provided IDs.
        """
        document, file_type = super(IrActionsReportXml, self).render_report(
            res_ids, name, data)

        report = self.search([('report_name', '=', name)], limit=1)
        behaviour = report.behaviour()[report.id]
        printer = behaviour['printer']

        can_print_report = self._can_print_report(
            behaviour, printer, document)

        if can_print_report:
            printer.print_document(report, document, report.report_type)
            return
        return document, file_type
