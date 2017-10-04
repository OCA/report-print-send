# -*- coding: utf-8 -*-
# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models, _


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    property_printing_action_id = fields.Many2one(
        comodel_name='printing.action',
        string='Default Behaviour',
        company_dependent=True,
    )
    printing_printer_id = fields.Many2one(
        comodel_name='printing.printer',
        string='Default Printer'
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
        report = self._get_report_from_name(report_name)
        if not report:
            return {}
        result = report.behaviour()[report]
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
            print_action = printing_act_obj.search([
                ('report_id', '=', report.id),
                ('user_id', '=', self.env.uid),
                ('action', '!=', 'user_default'),
            ], limit=1)
            if print_action:
                user_action = print_action.behaviour()
                action = user_action['action']
                if user_action['printer']:
                    printer = user_action['printer']

            result[report] = {
                'action': action,
                'printer': printer,
            }
        return result

    @api.multi
    def print_document(self, record_ids, data=None):
        """ Print a document, do not return the document file """
        document = self.with_context(
            must_skip_send_to_printer=True).render_qweb_pdf(
                record_ids, data=data)
        behaviour = self.behaviour()[self]
        printer = behaviour['printer']
        if not printer:
            raise exceptions.Warning(
                _('No printer configured to print this report.')
            )
        return printer.print_document(self, document, self.report_type)

    @api.multi
    def _can_print_report(self, behaviour, printer, document):
        """Predicate that decide if report can be sent to printer

        If you want to prevent `render_qweb_pdf` to send report you can set
        the `must_skip_send_to_printer` key to True in the context
        """
        if self.env.context.get('must_skip_send_to_printer'):
            return False
        if behaviour['action'] == 'server' and printer and document:
            return True
        return False

    @api.model
    def render_qweb_pdf(self, docids, data=None):
        """ Generate a PDF and returns it.

        If the action configured on the report is server, it prints the
        generated document as well.
        """
        document, doc_format = super(IrActionsReport, self).render_qweb_pdf(
            docids, data=data)

        behaviour = self.behaviour()[self]
        printer = behaviour['printer']
        can_print_report = self._can_print_report(behaviour, printer, document)

        if can_print_report:
            printer.print_document(self, document, self.report_type)

        return document, doc_format
