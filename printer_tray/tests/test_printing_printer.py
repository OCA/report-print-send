# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock
import tempfile
from openerp.tests.common import TransactionCase


model = 'openerp.addons.base_report_to_printer.printing'

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


class TestPrintingPrinter(TransactionCase):

    def setUp(self):
        super(TestPrintingPrinter, self).setUp()
        self.Model = self.env['printing.printer']
        self.printer = self.env['printing.printer'].create({
            'name': 'Printer',
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

    def new_tray(self, vals=None):
        values = self.tray_vals
        if vals is not None:
            values.update(vals)
        return self.env['printing.tray'].create(values)

    def build_ppd(self, input_slots=None):
        """
        Builds a fake PPD file declaring defined input slots
        """
        ppd_contents = ppd_header
        ppd_contents += ppd_input_slot_header
        if input_slots is not None:
            for input_slot in input_slots:
                ppd_contents += ppd_input_slot_body.format(
                    name=input_slot['name'],
                    text=input_slot['text'],
                )
        ppd_contents += ppd_input_slot_footer

        return ppd_contents

    def mock_cups_ppd(self, cups, file_name=None, input_slots=None):
        """
        Create a fake PPD file (if needed), then mock the getPPD3 method
        return value to give that file
        """
        if file_name is None:
            fd, file_name = tempfile.mkstemp()

        if file_name:
            ppd_contents = self.build_ppd(input_slots=input_slots)
            with open(file_name, 'w') as fp:
                fp.write(ppd_contents)

        cups.Connection().getPPD3.return_value = (200, 0, file_name)

    def test_print_options(self):
        """
        It should generate the right options dictionnary
        """
        report = self.env['ir.actions.report.xml'].search([], limit=1)
        action = self.env['printing.report.xml.action'].create({
            'user_id': self.env.user.id,
            'report_id': report.id,
            'action': 'server',
        })
        user_tray = self.new_tray({
            'system_name': 'User tray',
        })
        report_tray = self.new_tray({
            'system_name': 'Report tray',
        })
        action_tray = self.new_tray({
            'system_name': 'Action tray',
        })

        # No tray defined
        self.env.user.printer_tray_id = False
        report.printer_tray_id = False
        action.printer_tray_id = False
        options = self.Model.print_options(report, 'pdf')
        self.assertFalse('InputSlot' in options)

        # Only user tray is defined
        self.env.user.printer_tray_id = user_tray
        report.printer_tray_id = False
        action.printer_tray_id = False
        options = self.Model.print_options(report, 'pdf')
        self.assertEquals(options, {
            'InputSlot': 'User tray',
        })

        # Only report tray is defined
        self.env.user.printer_tray_id = False
        report.printer_tray_id = report_tray
        action.printer_tray_id = False
        options = self.Model.print_options(report, 'pdf')
        self.assertEquals(options, {
            'InputSlot': 'Report tray',
        })

        # Only action tray is defined
        self.env.user.printer_tray_id = False
        report.printer_tray_id = False
        action.printer_tray_id = action_tray
        options = self.Model.print_options(report, 'pdf')
        self.assertEquals(options, {
            'InputSlot': 'Action tray',
        })

        # All trays are defined
        self.env.user.printer_tray_id = user_tray
        report.printer_tray_id = report_tray
        action.printer_tray_id = action_tray
        options = self.Model.print_options(report, 'pdf')
        self.assertEquals(options, {
            'InputSlot': 'Action tray',
        })

    @mock.patch('%s.cups' % model)
    def test_update_printers(self, cups):
        """
        Check that the update_printers method calls _prepare_update_from_cups
        """
        self.mock_cups_ppd(cups, file_name=False)

        with mock.patch.object(
            self.Model, '_prepare_update_from_cups'
        ) as prepare_update_from_cups:
            self.Model.update_printers_status()
            prepare_update_from_cups.assert_called_once()

    @mock.patch('%s.cups' % model)
    def test_prepare_update_from_cups_no_ppd(self, cups):
        """
        Check that the tray_ids field has no value when no PPD is available
        """
        self.mock_cups_ppd(cups, file_name=False)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertFalse('tray_ids' in vals)

    @mock.patch('%s.cups' % model)
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
        cups_printer = connection.getPrinters()

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertFalse('tray_ids' in vals)

    @mock.patch('%s.cups' % model)
    def test_prepare_update_from_cups(self, cups):
        """
        Check the return value when adding a single tray
        """
        self.mock_cups_ppd(cups)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(vals['tray_ids'], [(0, 0, {
            'name': 'Auto (Default)',
            'system_name': 'Auto',
        })])

    @mock.patch('%s.cups' % model)
    def test_prepare_update_from_cups_with_multiple_trays(self, cups):
        """
        Check the return value when adding multiple trays at once
        """
        self.mock_cups_ppd(cups, input_slots=[
            {'name': 'Tray1', 'text': 'Tray 1'},
        ])

        connection = cups.Connection()
        cups_printer = connection.getPrinters()

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(vals['tray_ids'], [(0, 0, {
            'name': 'Auto (Default)',
            'system_name': 'Auto',
        }), (0, 0, {
            'name': 'Tray 1',
            'system_name': 'Tray1',
        })])

    @mock.patch('%s.cups' % model)
    def test_prepare_update_from_cups_already_known_trays(self, cups):
        """
        Check that calling the method twice doesn't create the trays multiple
        times
        """
        self.mock_cups_ppd(cups, input_slots=[
            {'name': 'Tray1', 'text': 'Tray 1'},
        ])

        connection = cups.Connection()
        cups_printer = connection.getPrinters()

        # Create a tray which is in the PPD file
        self.new_tray({'system_name': 'Tray1'})

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(vals['tray_ids'], [(0, 0, {
            'name': 'Auto (Default)',
            'system_name': 'Auto',
        })])

    @mock.patch('%s.cups' % model)
    def test_prepare_update_from_cups_unknown_trays(self, cups):
        """
        Check that trays which are not in the PPD file are removed from Odoo
        """
        self.mock_cups_ppd(cups)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()

        # Create a tray which is absent from the PPD file
        tray = self.new_tray()

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(vals['tray_ids'], [(0, 0, {
            'name': 'Auto (Default)',
            'system_name': 'Auto',
        }), (2, tray.id)])
