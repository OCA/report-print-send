# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import tempfile
import mock

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


model = 'odoo.addons.base_report_to_printer.models.printing_printer'
server_model = 'odoo.addons.base_report_to_printer.models.printing_server'


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
        self.report = self.env['ir.actions.report'].search([], limit=1)

    def new_record(self):
        return self.Model.create(self.printer_vals)

    def test_option_tray(self):
        """
        It should put the value in InputSlot
        """
        self.assertEqual(self.Model._set_option_tray(None, 'Test Tray'),
                         {'InputSlot': 'Test Tray'})
        self.assertEqual(self.Model._set_option_tray(None, False),
                         {})

    def test_option_noops(self):
        """
        Noops should return an empty dict
        """
        self.assertEqual(self.Model._set_option_action(None, 'printer'), {})
        self.assertEqual(self.Model._set_option_printer(None, self.Model), {})

    def test_option_doc_format(self):
        """
        Raw documents should set raw boolean.
        """
        self.assertEqual(self.Model._set_option_doc_format(None, 'raw'),
                         {'raw': 'True'})
        # Deprecate _set_option_format in v12.
        self.assertEqual(self.Model._set_option_format(None, 'raw'),
                         {'raw': 'True'})

        self.assertEqual(self.Model._set_option_doc_format(None, 'pdf'), {})
        # Deprecate _set_option_format in v12.
        self.assertEqual(self.Model._set_option_format(None, 'pdf'), {})

    def test_print_options(self):
        """ It should generate the right options dictionnary """
        # TODO: None here used as report - tests here should be merged
        # with tests in test_printing_printer_tray from when modules merged
        report = self.env['ir.actions.report'].search([], limit=1)
        self.assertEqual(self.Model.print_options(
            doc_format='raw'), {'raw': 'True'}
        )
        self.assertEqual(self.Model.print_options(
            report, doc_format='pdf', copies=2), {'copies': '2'}
        )
        self.assertEqual(self.Model.print_options(
            report, doc_format='raw', copies=2),
            {'raw': 'True', 'copies': '2'}
        )
        self.assertTrue('InputSlot' in self.Model.print_options(report,
                                                                tray='Test'))

    @mock.patch('%s.cups' % server_model)
    def test_print_report(self, cups):
        """ It should print a report through CUPS """
        fd, file_name = tempfile.mkstemp()
        with mock.patch('%s.mkstemp' % model) as mkstemp:
            mkstemp.return_value = fd, file_name
            printer = self.new_record()
            printer.print_document(self.report, b'content to print',
                                   doc_format='pdf')
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
                    self.report, b'content to print', doc_format='pdf')

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
        self.assertEqual(other_printer, self.Model.get_default())

    def test_unset_default(self):
        """ It should unset the default state of the printer """
        printer = self.new_record()
        self.assertTrue(printer.default)
        printer.unset_default()
        self.assertFalse(printer.default)

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
