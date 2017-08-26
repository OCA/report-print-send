# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock
from odoo.tests.common import HttpCase
from odoo import exceptions


class StopTest(Exception):
    pass


class TestReport(HttpCase):

    def setUp(self):
        super(TestReport, self).setUp()
        self.Model = self.env['report']
        self.server = self.env['printing.server'].create({})
        self.report_vals = {}

    def new_record(self):
        return self.Model.create(self.report_vals)

    def new_printer(self):
        return self.env['printing.printer'].create({
            'name': 'Printer',
            'server_id': self.server.id,
            'system_name': 'Sys Name',
            'default': True,
            'status': 'unknown',
            'status_message': 'Msg',
            'model': 'res.users',
            'location': 'Location',
            'uri': 'URI',
        })

    def test_can_print_report_context_skip(self):
        """ It should return False based on context """
        rec_id = self.new_record().with_context(
            must_skip_send_to_printer=True
        )
        res = rec_id._can_print_report(
            {'action': 'server'}, True, True
        )
        self.assertFalse(res)

    def test_can_print_report_true(self):
        """ It should return True when server print allowed """
        res = self.new_record()._can_print_report(
            {'action': 'server'}, True, True
        )
        self.assertTrue(res)

    def test_can_print_report_false(self):
        """ It should return False when server print not allowed """
        res = self.new_record()._can_print_report(
            {'action': 'server'}, True, False
        )
        self.assertFalse(res)

    def test_get_pdf_not_printable(self):
        """ It should print the report, only if it is printable
        """
        with mock.patch('odoo.addons.base_report_to_printer.models.'
                        'printing_printer.PrintingPrinter.'
                        'print_document') as print_document:
            report = self.env['ir.actions.report.xml'].search([
                ('report_type', '=', 'qweb-pdf'),
            ], limit=1)
            records = self.env[report.model].search([], limit=5)
            self.env['report'].get_pdf(records.ids, report.report_name)
            print_document.assert_not_called()

    def test_get_pdf_printable(self):
        """ It should print the report, only if it is printable
        """
        with mock.patch('odoo.addons.base_report_to_printer.models.'
                        'printing_printer.PrintingPrinter.'
                        'print_document') as print_document:
            report = self.env['ir.actions.report.xml'].search([
                ('report_type', '=', 'qweb-pdf'),
            ], limit=1)
            report.property_printing_action_id.action_type = 'server'
            report.printing_printer_id = self.new_printer()
            records = self.env[report.model].search([], limit=5)
            document = self.env['report'].get_pdf(
                records.ids, report.report_name)
            print_document.assert_called_once_with(
                report, document, report.report_type)

    def test_print_document_not_printable(self):
        """ It should print the report, regardless of the defined behaviour """
        report = self.env['ir.actions.report.xml'].search([
            ('report_type', '=', 'qweb-pdf'),
        ], limit=1)
        report.printing_printer_id = self.new_printer()
        records = self.env[report.model].search([], limit=5)

        with mock.patch('odoo.addons.base_report_to_printer.models.'
                        'printing_printer.PrintingPrinter.'
                        'print_document') as print_document:
            self.env['report'].print_document(records.ids, report.report_name)
            print_document.assert_called_once()

    def test_print_document_printable(self):
        """ It should print the report, regardless of the defined behaviour """
        report = self.env['ir.actions.report.xml'].search([
            ('report_type', '=', 'qweb-pdf'),
        ], limit=1)
        report.property_printing_action_id.action_type = 'server'
        report.printing_printer_id = self.new_printer()
        records = self.env[report.model].search([], limit=5)

        with mock.patch('odoo.addons.base_report_to_printer.models.'
                        'printing_printer.PrintingPrinter.'
                        'print_document') as print_document:
            self.env['report'].print_document(records.ids, report.report_name)
            print_document.assert_called_once()

    def test_print_document_no_printer(self):
        """ It should raise an error """
        report = self.env['ir.actions.report.xml'].search([
            ('report_type', '=', 'qweb-pdf'),
        ], limit=1)
        records = self.env[report.model].search([], limit=5)

        with self.assertRaises(exceptions.UserError):
            self.env['report'].print_document(records.ids, report.report_name)
