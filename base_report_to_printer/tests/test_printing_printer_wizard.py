# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.tests.common import TransactionCase
from openerp.exceptions import UserError

from openerp.addons.base_report_to_printer.models.printing_printer import (
    CUPS_HOST,
    CUPS_PORT,
)


model = '%s.%s' % ('openerp.addons.base_report_to_printer.wizards',
                   'printing_printer_update_wizard')


class StopTest(Exception):
    pass


class TestPrintingPrinterWizard(TransactionCase):

    def setUp(self):
        super(TestPrintingPrinterWizard, self).setUp()
        self.Model = self.env['printing.printer.update.wizard']
        self.printer_vals = {
            'printer-info': 'Info',
            'printer-make-and-model': 'Make and Model',
            'printer-location': "location",
            'device-uri': 'URI',
        }

    def _record_vals(self, sys_name='sys_name'):
        return {
            'name': self.printer_vals['printer-info'],
            'system_name': sys_name,
            'model': self.printer_vals['printer-make-and-model'],
            'location': self.printer_vals['printer-location'],
            'uri': self.printer_vals['device-uri'],
        }

    @mock.patch('%s.cups' % model)
    def test_action_ok_inits_connection(self, cups):
        """ It should initialize CUPS connection """
        try:
            self.Model.action_ok()
        except:
            pass
        cups.Connection.assert_called_once_with(
            CUPS_HOST, CUPS_PORT,
        )

    @mock.patch('%s.cups' % model)
    def test_action_ok_gets_printers(self, cups):
        """ It should get printers from CUPS """
        cups.Connection().getPrinters.return_value = {
            'sys_name': self.printer_vals,
        }
        self.Model.action_ok()
        cups.Connection().getPrinters.assert_called_once_with()

    @mock.patch('%s.cups' % model)
    def test_action_ok_raises_warning_on_error(self, cups):
        """ It should raise Warning on any error """
        cups.Connection.side_effect = StopTest
        with self.assertRaises(UserError):
            self.Model.action_ok()

    @mock.patch('%s.cups' % model)
    def test_action_ok_creates_new_printer(self, cups):
        """ It should create new printer w/ proper vals """
        cups.Connection().getPrinters.return_value = {
            'sys_name': self.printer_vals,
        }
        self.Model.action_ok()
        rec_id = self.env['printing.printer'].search([
            ('system_name', '=', 'sys_name')
        ],
            limit=1,
        )
        self.assertTrue(rec_id)
        for key, val in self._record_vals().iteritems():
            self.assertEqual(
                val, getattr(rec_id, key),
            )

    @mock.patch('%s.cups' % model)
    def test_action_ok_skips_existing_printer(self, cups):
        """ It should not recreate existing printers """
        cups.Connection().getPrinters.return_value = {
            'sys_name': self.printer_vals,
        }
        self.env['printing.printer'].create(
            self._record_vals()
        )
        self.Model.action_ok()
        res_ids = self.env['printing.printer'].search([
            ('system_name', '=', 'sys_name')
        ])
        self.assertEqual(
            1, len(res_ids),
        )
