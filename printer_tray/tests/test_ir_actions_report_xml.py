# -*- coding: utf-8 -*-
# Copyright 2017 SYLEAM Info Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestIrActionsReportXml(TransactionCase):
    def test_onchange_printer_tray_id_empty(self):
        action = self.env['ir.actions.report.xml'].new(
            {'printer_input_tray_id': False,
             'printer_output_tray_id': False})
        action.onchange_printing_printer_id()
        self.assertFalse(action.printer_input_tray_id)
        self.assertFalse(action.printer_output_tray_id)

    def test_onchange_printer_tray_id_not_empty(self):
        server = self.env['printing.server'].create({})
        printer = self.env['printing.printer'].create({
            'name': 'Printer',
            'server_id': server.id,
            'system_name': 'Sys Name',
            'default': True,
            'status': 'unknown',
            'status_message': 'Msg',
            'model': 'res.users',
            'location': 'Location',
            'uri': 'URI',
        })
        tray_in = self.env['printing.tray.input'].create({
            'name': 'Input tray',
            'system_name': 'TrayName IN',
            'printer_id': printer.id,
        })
        tray_out = self.env['printing.tray.output'].create({
            'name': 'Output tray',
            'system_name': 'TrayName OUT',
            'printer_id': printer.id,
        })

        action = self.env['ir.actions.report.xml'].new(
            {'printer_input_tray_id': tray_in.id,
             'printer_output_tray_id': tray_out.id})
        self.assertEqual(action.printer_input_tray_id, tray_in)
        self.assertEqual(action.printer_output_tray_id, tray_out)
        action.onchange_printing_printer_id()
        self.assertFalse(action.printer_input_tray_id)
        self.assertFalse(action.printer_output_tray_id)
