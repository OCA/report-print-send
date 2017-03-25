# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock
from openerp.tests.common import TransactionCase


class StopTest(Exception):
    pass


class TestReport(TransactionCase):

    def setUp(self):
        super(TestReport, self).setUp()
        self.Model = self.env['report']
        self.server = self.env['printing.server'].create({})
        self.report_vals = {}

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

    def test_generate_email(self):
        """ Check that generating an email doesn't print the report """
        report = self.env['ir.actions.report.xml'].search([
            ('report_type', '=', 'qweb-pdf'),
        ], limit=1)
        report.property_printing_action_id.type = 'server'
        report.printing_printer_id = self.new_printer()
        records = self.env[report.model].search([], limit=5)

        model = self.env['ir.model'].search([('model', '=', report.model)])
        mail_template = self.env['mail.template'].create({
            'model_id': model.id,
            'report_template': report.id,
        })

        with mock.patch('openerp.addons.base_report_to_printer.models.'
                        'printing_printer.PrintingPrinter.'
                        'print_document') as print_document:
            print_document.side_effect = Exception

            # Check that the report is printed when called directly
            with self.assertRaises(Exception):
                self.env['report'].get_pdf(records.ids, report.report_name)

            # Check that the same report is not printed when called for email
            mail_template.generate_email(records.ids)
