# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.tests.common import TransactionCase

from openerp.addons.base_report_to_printer.models.printing_printer import (
    CUPS_HOST,
    CUPS_PORT,
)


model = 'openerp.addons.base_report_to_printer.models.printing_printer'


class TestPrintingPrinter(TransactionCase):

    def setUp(self):
        super(TestPrintingPrinter, self).setUp()
        self.Model = self.env['printing.printer']
        self.printer_vals = {
            'name': 'Printer',
            'system_name': 'Sys Name',
            'default': True,
            'status': 'unknown',
            'status_message': 'Msg',
            'model': 'res.users',
            'location': 'Location',
            'uri': 'URI',
        }

    def new_record(self):
        return self.Model.create(self.printer_vals)

    @mock.patch('%s.cups' % model)
    def test_update_printers_status_error(self, cups):
        """ It should catch any exception from CUPS and update status """
        cups.Connection.side_effect = Exception
        rec_id = self.new_record()
        self.Model.update_printers_status()
        self.assertEqual(
            'server-error', rec_id.status,
        )

    @mock.patch('%s.cups' % model)
    def test_update_printers_status_inits_cups(self, cups):
        """ It should init CUPS connection """
        self.new_record()
        self.Model.update_printers_status()
        cups.Connection.assert_called_once_with(
            CUPS_HOST, CUPS_PORT,
        )

    @mock.patch('%s.cups' % model)
    def test_update_printers_status_gets_all_printers(self, cups):
        """ It should get all printers from CUPS server """
        self.new_record()
        self.Model.update_printers_status()
        cups.Connection().getPrinters.assert_called_once_with()

    @mock.patch('%s.cups' % model)
    def test_update_printers_status_gets_printer(self, cups):
        """ It should get printer from CUPS by system_name """
        rec_id = self.new_record()
        self.Model.update_printers_status()
        cups.Connection().getPrinters().get.assert_called_once_with(
            rec_id.system_name,
        )

    @mock.patch('%s.cups' % model)
    def test_update_printers_status_search(self, cups):
        """ It should search all when no domain """
        with mock.patch.object(self.Model, 'search') as search:
            self.Model.update_printers_status()
            search.assert_called_once_with([])

    @mock.patch('%s.cups' % model)
    def test_update_printers_status_search_domain(self, cups):
        """ It should use specific domain for search """
        with mock.patch.object(self.Model, 'search') as search:
            expect = [('id', '>', 0)]
            self.Model.update_printers_status(expect)
            search.assert_called_once_with(expect)

    @mock.patch('%s.cups' % model)
    def test_update_printers_status_update_printer(self, cups):
        """ It should update from CUPS when printer identified """
        with mock.patch.object(self.Model, 'search') as search:
            printer_mk = mock.MagicMock()
            search.return_value = [printer_mk]
            self.Model.update_printers_status()
            printer_mk.update_from_cups.assert_called_once_with(
                cups.Connection(),
                cups.Connection().getPrinters().get(),
            )

    @mock.patch('%s.cups' % model)
    def test_update_printers_status_update_unavailable(self, cups):
        """ It should update status when printer is unavailable """
        rec_id = self.new_record()
        cups.Connection().getPrinters().get.return_value = False
        self.Model.update_printers_status()
        self.assertEqual(
            'unavailable', rec_id.status,
        )
