# -*- coding: utf-8 -*-
# Copyright (c) 2014 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, exceptions, _, api


class Report(models.Model):
    _inherit = 'report'

    @api.model
    def print_document(self, record_ids, report_name, html=None, data=None):
        """ Print a document, do not return the document file """
        document = self.with_context(must_skip_send_to_printer=True).get_pdf(
            record_ids, report_name, html=html, data=data)
        report = self._get_report_from_name(report_name)
        behaviour = report.behaviour()[report.id]
        printer = behaviour['printer']
        if not printer:
            raise exceptions.Warning(
                _('No printer configured to print this report.')
            )
        return printer.print_document(
            report_name,
            document,
            report.report_type,
            copies=self.env.context.get('report_copies')
        )

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
    def get_pdf(self, docids, report_name, html=None, data=None):
        """ Generate a PDF and returns it.

        If the action configured on the report is server, it prints the
        generated document as well.
        """
        document = super(Report, self).get_pdf(
            docids, report_name, html=html, data=data)

        report = self._get_report_from_name(report_name)
        behaviour = report.behaviour()[report.id]
        printer = behaviour['printer']
        can_print_report = self._can_print_report(behaviour, printer, document)

        if can_print_report:
            printer.print_document(report_name, document, report.report_type)

        return document
