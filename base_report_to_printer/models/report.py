# -*- coding: utf-8 -*-
# Copyright (c) 2014 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, exceptions, _, api


class Report(models.Model):
    _inherit = 'report'

    @api.v7
    def print_document(self, cr, uid, ids, report_name, html=None,
                       data=None, context=None):
        """ Print a document, do not return the document file """
        if context is None:
            context = self.pool['res.users'].context_get(cr, uid)
        local_context = context.copy()
        local_context['must_skip_send_to_printer'] = True
        document = self.get_pdf(cr, uid, ids, report_name,
                                html=html, data=data, context=local_context)
        report = self._get_report_from_name(cr, uid, report_name)
        behaviour = report.behaviour()[report.id]
        printer = behaviour['printer']
        if not printer:
            raise exceptions.Warning(
                _('No printer configured to print this report.')
            )
        return printer.with_context(context).print_document(
            report, document, report.report_type)

    @api.v8
    def print_document(self, records, report_name, html=None, data=None):
        return self._model.print_document(
            self._cr, self._uid,
            records.ids, report_name,
            html=html, data=data, context=self._context)

    def _can_print_report(self, cr, uid, ids, behaviour, printer, document,
                          context=None):
        """Predicate that decide if report can be sent to printer

        If you want to prevent `get_pdf` to send report you can set
        the `must_skip_send_to_printer` key to True in the context
        """
        if context is not None and context.get('must_skip_send_to_printer'):
            return False
        if behaviour['action'] == 'server' and printer and document:
            return True
        return False

    @api.v7
    def get_pdf(self, cr, uid, ids, report_name, html=None,
                data=None, context=None):
        """ Generate a PDF and returns it.

        If the action configured on the report is server, it prints the
        generated document as well.
        """
        document = super(Report, self).get_pdf(cr, uid, ids, report_name,
                                               html=html, data=data,
                                               context=context)
        report = self._get_report_from_name(cr, uid, report_name)
        behaviour = report.behaviour()[report.id]
        printer = behaviour['printer']
        can_print_report = self._can_print_report(cr, uid, ids,
                                                  behaviour, printer, document,
                                                  context=context)
        if can_print_report:
            printer.print_document(report, document, report.report_type)
        return document

    @api.v8
    def get_pdf(self, records, report_name, html=None, data=None):
        return self._model.get_pdf(self._cr, self._uid,
                                   records.ids, report_name,
                                   html=html, data=data, context=self._context)
