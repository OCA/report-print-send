# -*- coding: utf-8 -*-
# Copyright (c) 2014 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, exceptions, _, api


class Report(models.Model):
    _inherit = 'report'

    @api.multi
    def print_document(self, report_name, html=None, data=None):
        """ Print a document, do not return the document file """
        res = []
        context = self.env.context

        if context is None:
            context = self.env['res.users'].context_get()

        local_context = context.copy()
        local_context['must_skip_send_to_printer'] = True
        object_to_print = self.env[local_context['active_model']].browse(local_context['active_ids'])

        for rec_id in self.with_context(local_context):
            document = self.env['report'].get_pdf(object_to_print.ids, report_name, html=html, data=data)
            report = self._get_report_from_name(report_name)
            behaviour = report.behaviour()[report.id]
            printer = behaviour['printer']
            if not printer:
                raise exceptions.Warning(
                    _('No printer configured to print this report.')
                )
            res.append(
                printer.print_document(report, document, report.report_type)
            )
        return all(res)

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
