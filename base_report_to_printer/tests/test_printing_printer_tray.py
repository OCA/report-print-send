# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import errno
import mock
import tempfile
from odoo.tests.common import TransactionCase


model = 'odoo.addons.base_report_to_printer.models.printing_printer'
server_model = 'odoo.addons.base_report_to_printer.models.printing_server'

ppd_header = '*PPD-Adobe: "4.3"'
ppd_input_slot_header = """
*OpenUI *InputSlot: PickOne
*DefaultInputSlot: Auto
*InputSlot Auto/Auto (Default): "
    << /DeferredMediaSelection true /ManualFeed false
        /MediaPosition null /MediaType null >> setpagedevice
        userdict /TSBMediaType 0 put"
*End
"""
ppd_input_slot_body = """
*InputSlot {name}/{text}: "
    << /DeferredMediaSelection true /ManualFeed false
        /MediaPosition null /MediaType null >> setpagedevice
        userdict /TSBMediaType 0 put"
*End
"""
ppd_input_slot_footer = """
*CloseUI: *InputSlot
"""
ppd_output_slot_header = """
*OpenUI *OutputBin/Output Tray: PickOne
*OrderDependency: 40 AnySetup *OutputBin
*DefaultOutputBin: Default
*OutputBin Default/Default: "
    << /OutputType (Default) >> setpagedevice"
"""
ppd_output_slot_body = """
*OutputBin {name}/{text}: "
    << /OutputType (Bin{nb}) >> setpagedevice"
"""
ppd_output_slot_footer = """
*CloseUI: *OutputBin
"""


class TestPrintingPrinter(TransactionCase):

    def setUp(self):
        super(TestPrintingPrinter, self).setUp()
        self.Model = self.env['printing.printer']
        self.ServerModel = self.env['printing.server']
        self.server = self.env['printing.server'].create({})
        self.printer = self.env['printing.printer'].create({
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
        self.tray_vals = {
            'name': 'Tray',
            'system_name': 'TrayName',
            'printer_id': self.printer.id,
        }

    def new_tray(self, tray_type='input', vals=None):
        values = self.tray_vals
        if vals is not None:
            values.update(vals)
        return self.env['printing.tray.' + tray_type].create(values)

    def build_ppd(self, trays=None):
        """
        Builds a fake PPD file declaring defined input slots
        """
        ppd_contents = ppd_header
        ppd_contents += ppd_input_slot_header
        if trays is not None:
            for slot in trays:
                ppd_contents += ppd_input_slot_body.format(
                    name=slot['name'],
                    text=slot['text'],
                )
        ppd_contents += ppd_input_slot_footer
        ppd_contents += ppd_output_slot_header
        if trays is not None:
            for slot in trays:
                ppd_contents += ppd_output_slot_body.format(
                    name=slot['name'],
                    text=slot['text'],
                    nb=slot['text'][-1],
                )
        ppd_contents += ppd_output_slot_footer

        return ppd_contents

    def mock_cups_ppd(self, cups, file_name=None, trays=None):
        """
        Create a fake PPD file (if needed), then mock the getPPD3 method
        return value to give that file
        """
        if file_name is None:
            fd, file_name = tempfile.mkstemp()

        if file_name:
            ppd_contents = self.build_ppd(trays=trays)
            with open(file_name, 'w') as fp:
                fp.write(ppd_contents)

        cups.Connection().getPPD3.return_value = (200, 0, file_name)
        cups.Connection().getPrinters.return_value = {
            self.printer.system_name: {
                'printer-info': 'info',
                'printer-uri-supported': 'uri',
            },
        }

    @mock.patch('%s.cups' % server_model)
    def test_update_printers(self, cups):
        """
        Check that the update_printers method calls _prepare_update_from_cups
        """
        self.mock_cups_ppd(cups, file_name=False)

        self.assertEqual(self.printer.name, 'Printer')
        self.ServerModel.update_printers()
        self.assertEqual(self.printer.name, 'info')

    @mock.patch('%s.cups' % server_model)
    def test_prepare_update_from_cups_no_ppd(self, cups):
        """
        Check that the tray_ids field has no value when no PPD is available
        """
        self.mock_cups_ppd(cups, file_name=False)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertFalse('input_tray_ids' in vals)
        self.assertFalse('output_tray_ids' in vals)

    @mock.patch('%s.cups' % server_model)
    def test_prepare_update_from_cups_empty_ppd(self, cups):
        """
        Check that the tray_ids field has no value when the PPD file has
        no input slot declared
        """
        fd, file_name = tempfile.mkstemp()
        self.mock_cups_ppd(cups, file_name=file_name)
        # Replace the ppd file's contents by an empty file
        with open(file_name, 'w') as fp:
            fp.write(ppd_header)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertFalse('input_tray_ids' in vals)
        self.assertFalse('output_tray_ids' in vals)

    @mock.patch('%s.cups' % server_model)
    @mock.patch('os.unlink')
    def test_prepare_update_from_cups_unlink_error(self, os_unlink, cups):
        """
        When OSError other than ENOENT is encountered, the exception is raised
        """
        # Break os.unlink
        os_unlink.side_effect = OSError(errno.EIO, 'Error')

        self.mock_cups_ppd(cups)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        with self.assertRaises(OSError):
            self.printer._prepare_update_from_cups(connection, cups_printer)

    @mock.patch('%s.cups' % server_model)
    @mock.patch('os.unlink')
    def test_prepare_update_from_cups_unlink_error_enoent(
            self, os_unlink, cups):
        """
        When a ENOENT error is encountered, the file has already been unlinked
        This is not an issue, as we were trying to delete the file.
        The update can continue.
        """
        # Break os.unlink
        os_unlink.side_effect = OSError(errno.ENOENT, 'Error')

        self.mock_cups_ppd(cups)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(vals['input_tray_ids'], [(0, 0, {
            'name': 'Auto (Default)',
            'system_name': 'Auto',
        })])
        self.assertEqual(vals['output_tray_ids'], [(0, 0, {
            'name': 'Default',
            'system_name': 'Default',
        })])

    @mock.patch('%s.cups' % server_model)
    def test_prepare_update_from_cups(self, cups):
        """
        Check the return value when adding a single tray
        """
        self.mock_cups_ppd(cups)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(vals['input_tray_ids'], [(0, 0, {
            'name': 'Auto (Default)',
            'system_name': 'Auto',
        })])
        self.assertEqual(vals['output_tray_ids'], [(0, 0, {
            'name': 'Default',
            'system_name': 'Default',
        })])

    @mock.patch('%s.cups' % server_model)
    def test_prepare_update_from_cups_with_multiple_trays(self, cups):
        """
        Check the return value when adding multiple trays at once
        """
        self.mock_cups_ppd(cups, trays=[
            {'name': 'Tray1', 'text': 'Tray 1'},
        ])

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertItemsEqual(vals['input_tray_ids'], [(0, 0, {
            'name': 'Auto (Default)',
            'system_name': 'Auto',
        }), (0, 0, {
            'name': 'Tray 1',
            'system_name': 'Tray1',
        })])
        self.assertItemsEqual(vals['output_tray_ids'], [(0, 0, {
            'name': 'Default',
            'system_name': 'Default',
        }), (0, 0, {
            'name': 'Tray 1',
            'system_name': 'Tray1',
        })])

    @mock.patch('%s.cups' % server_model)
    def test_prepare_update_from_cups_already_known_trays(self, cups):
        """
        Check that calling the method twice doesn't create the trays multiple
        times
        """
        self.mock_cups_ppd(cups, trays=[
            {'name': 'Tray1', 'text': 'Tray 1'},
        ])

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        # Create a tray which is in the PPD file
        self.new_tray('input', {'system_name': 'Tray1'})
        self.new_tray('output', {'system_name': 'Tray1'})

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(vals['input_tray_ids'], [(0, 0, {
            'name': 'Auto (Default)',
            'system_name': 'Auto',
        })])
        self.assertEqual(vals['output_tray_ids'], [(0, 0, {
            'name': 'Default',
            'system_name': 'Default',
        })])

    @mock.patch('%s.cups' % server_model)
    def test_prepare_update_from_cups_unknown_trays(self, cups):
        """
        Check that trays which are not in the PPD file are removed from Odoo
        """
        self.mock_cups_ppd(cups)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        # Create a tray which is absent from the PPD file
        input_tray = self.new_tray()
        output_tray = self.new_tray('output')

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(vals['input_tray_ids'], [(0, 0, {
            'name': 'Auto (Default)',
            'system_name': 'Auto',
        }), (2, input_tray.id)])
        self.assertEqual(vals['output_tray_ids'], [(0, 0, {
            'name': 'Default',
            'system_name': 'Default',
        }), (2, output_tray.id)])
