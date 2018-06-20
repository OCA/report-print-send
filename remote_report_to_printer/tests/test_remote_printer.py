# Copyright (c) 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestRemotePrinter(TransactionCase):

    def setUp(self):
        super().setUp()
        name = 'testing_remote_server'
        self.remote = self.env['res.remote'].search([('name', '=', name)])
        if not self.remote:
            self.remote = self.env['res.remote'].create({
                'name': name,
                'ip': '127.0.0.1',
            })
        self.server = self.env['printing.server'].create({
            'name': 'Server',
            'address': 'localhost',
            'port': 631,
        })
        self.printer_1 = self.env['printing.printer'].create({
            'name': 'Printer 1',
            'system_name': 'P1',
            'server_id': self.server.id,
        })
        self.printer_2 = self.env['printing.printer'].create({
            'name': 'Printer 2',
            'system_name': 'P2',
            'server_id': self.server.id,
        })
        self.tray_1 = self.env['printing.tray'].create({
            'name': 'Tray',
            'system_name': 'P2',
            'printer_id': self.printer_1.id,
        })

    def test_constrain(self):
        self.env['res.remote.printer'].create({
            'remote_id': self.remote.id,
            'printer_id': self.printer_1.id,
            'is_default': True,
        })
        with self.assertRaises(ValidationError):
            self.env['res.remote.printer'].create({
                'remote_id': self.remote.id,
                'printer_id': self.printer_2.id,
                'is_default': True,
            })

    def test_onchange_printer(self):
        remote_printer = self.env['res.remote.printer'].create({
            'remote_id': self.remote.id,
            'printer_id': self.printer_1.id,
            'printer_tray_id': self.tray_1.id,
        })
        self.assertTrue(remote_printer.printer_tray_id)
        remote_printer.printer_id = self.printer_2
        remote_printer._onchange_printing_printer_id()
        self.assertFalse(remote_printer.printer_tray_id)
