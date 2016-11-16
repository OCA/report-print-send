# -*- coding: utf-8 -*-
# Copyright 2017 SYLEAM Info Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestIrActionsReportXml(TransactionCase):
    def test_onchange_printer_tray_id_empty(self):
        action = self.env['ir.actions.report.xml'].new(
            {'printer_tray_id': False})
        action.onchange_printing_printer_id()
        self.assertFalse(action.printer_tray_id)

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
        tray = self.env['printing.tray'].create({
            'name': 'Tray',
            'system_name': 'TrayName',
            'printer_id': printer.id,
        })

        action = self.env['ir.actions.report.xml'].new(
            {'printer_tray_id': tray.id})
        self.assertEqual(action.printer_tray_id, tray)
        action.onchange_printing_printer_id()
        self.assertFalse(action.printer_tray_id)
