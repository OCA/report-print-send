# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import tempfile
import mock

from openerp.exceptions import UserError
from openerp.tests.common import TransactionCase


model = 'openerp.addons.base_report_to_printer.models.printing_printer'
server_model = 'openerp.addons.base_report_to_printer.models.printing_server'


class TestPrintingPrinter(TransactionCase):

    def setUp(self):
        super(TestPrintingPrinter, self).setUp()
        self.Model = self.env['printing.printer']
        self.ServerModel = self.env['printing.server']
        self.server = self.env['printing.server'].create({})
        self.printer_vals = {
            'name': 'Printer',
            'server_id': self.server.id,
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

    @mock.patch('%s.cups' % server_model)
    def test_update_printers_status_error(self, cups):
        """ It should catch any exception from CUPS and update status """
        cups.Connection.side_effect = Exception
        rec_id = self.new_record()
        self.Model.update_printers_status()
        self.assertEqual(
            'server-error', rec_id.status,
        )

    @mock.patch('%s.cups' % server_model)
    def test_update_printers_status_inits_cups(self, cups):
        """ It should init CUPS connection """
        self.new_record()
        self.Model.update_printers_status()
        cups.Connection.assert_called_once_with(
            host=self.server.address, port=self.server.port,
        )

    @mock.patch('%s.cups' % server_model)
    def test_update_printers_status_gets_all_printers(self, cups):
        """ It should get all printers from CUPS server """
        self.new_record()
        self.Model.update_printers_status()
        cups.Connection().getPrinters.assert_called_once_with()

    @mock.patch('%s.cups' % server_model)
    def test_update_printers_status_gets_printer(self, cups):
        """ It should get printer from CUPS by system_name """
        self.new_record()
        self.Model.update_printers_status()
        cups.Connection().getPrinters.assert_called_once_with()

    @mock.patch('%s.cups' % server_model)
    def test_update_printers_status_search(self, cups):
        """ It should search all when no domain """
        with mock.patch.object(self.Model, 'search') as search:
            self.Model.update_printers_status()
            search.assert_called_once_with([])

    @mock.patch('%s.cups' % server_model)
    def test_update_printers_status_search_domain(self, cups):
        """ It should use specific domain for search """
        with mock.patch.object(self.Model, 'search') as search:
            expect = [('id', '>', 0)]
            self.Model.update_printers_status(expect)
            search.assert_called_once_with(expect)

    @mock.patch('%s.cups' % server_model)
    def test_update_printers_status_update_printer(self, cups):
        """ It should update from CUPS when printer identified """
        printer = self.new_record()
        printer.update_from_cups(None, None)
        cups.Connection().getPrinters.assert_called_once_with()

    @mock.patch('%s.cups' % server_model)
    def test_update_printers_status_update_unavailable(self, cups):
        """ It should update status when printer is unavailable """
        rec_id = self.new_record()
        cups.Connection().getPrinters().get.return_value = False
        self.Model.update_printers_status()
        self.assertEqual(
            'unavailable', rec_id.status,
        )

    def test_printing_options(self):
        """ It should generate the right options dictionnary """
        self.assertEquals(self.Model.print_options('report', 'raw'), {
            'raw': 'True',
        })
        self.assertEquals(self.Model.print_options('report', 'pdf', 2), {
            'copies': '2',
        })
        self.assertEquals(self.Model.print_options('report', 'raw', 2), {
            'raw': 'True',
            'copies': '2',
        })

    @mock.patch('%s.cups' % server_model)
    def test_print_report(self, cups):
        """ It should print a report through CUPS """
        fd, file_name = tempfile.mkstemp()
        with mock.patch('%s.mkstemp' % model) as mkstemp:
            mkstemp.return_value = fd, file_name
            printer = self.new_record()
            printer.print_document('report_name', 'content to print', 'pdf')
            cups.Connection().printFile.assert_called_once_with(
                printer.system_name,
                file_name,
                file_name,
                options={})

    @mock.patch('%s.cups' % server_model)
    def test_print_report_error(self, cups):
        """ It should print a report through CUPS """
        cups.Connection.side_effect = Exception
        fd, file_name = tempfile.mkstemp()
        with mock.patch('%s.mkstemp' % model) as mkstemp:
            mkstemp.return_value = fd, file_name
            printer = self.new_record()
            with self.assertRaises(UserError):
                printer.print_document(
                    'report_name', 'content to print', 'pdf')

    @mock.patch('%s.cups' % server_model)
    def test_print_file(self, cups):
        """ It should print a file through CUPS """
        file_name = 'file_name'
        printer = self.new_record()
        printer.print_file(file_name, 'pdf')
        cups.Connection().printFile.assert_called_once_with(
            printer.system_name,
            file_name,
            file_name,
            options={})

    @mock.patch('%s.cups' % server_model)
    def test_print_file_error(self, cups):
        """ It should print a file through CUPS """
        cups.Connection.side_effect = Exception
        file_name = 'file_name'
        printer = self.new_record()
        with self.assertRaises(UserError):
            printer.print_file(file_name)

    def test_set_default(self):
        """ It should set a single record as default """
        printer = self.new_record()
        self.assertTrue(printer.default)
        other_printer = self.new_record()
        other_printer.set_default()
        self.assertFalse(printer.default)
        self.assertTrue(other_printer.default)
        # Check that calling the method on an empty recordset does nothing
        self.Model.set_default()
        self.assertEquals(other_printer, self.Model.get_default())

    @mock.patch('%s.cups' % server_model)
    def test_cancel_all_jobs(self, cups):
        """ It should cancel all jobs """
        printer = self.new_record()
        printer.action_cancel_all_jobs()
        cups.Connection().cancelAllJobs.assert_called_once_with(
            name=printer.system_name,
            purge_jobs=False,
        )

    @mock.patch('%s.cups' % server_model)
    def test_cancel_and_purge_all_jobs(self, cups):
        """ It should cancel all jobs """
        printer = self.new_record()
        printer.cancel_all_jobs(purge_jobs=True)
        cups.Connection().cancelAllJobs.assert_called_once_with(
            name=printer.system_name,
            purge_jobs=True,
        )

    @mock.patch('%s.cups' % server_model)
    def test_enable_printer(self, cups):
        """ It should enable the printer """
        printer = self.new_record()
        printer.enable()
        cups.Connection().enablePrinter.assert_called_once_with(
            printer.system_name)

    @mock.patch('%s.cups' % server_model)
    def test_disable_printer(self, cups):
        """ It should disable the printer """
        printer = self.new_record()
        printer.disable()
        cups.Connection().disablePrinter.assert_called_once_with(
            printer.system_name)
