# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


@common.at_install(False)
@common.post_install(True)
class TestResUsers(common.TransactionCase):

    def setUp(self):
        super(TestResUsers, self).setUp()
        self.user_vals = {'name': 'Test',
                          'login': 'login',
                          }

    def new_record(self):
        return self.env['res.users'].create(self.user_vals)

    def test_available_action_types_excludes_user_default(self):
        """ It should not contain `user_default` in avail actions """
        self.user_vals['printing_action'] = 'user_default'
        with self.assertRaises(ValueError):
            self.new_record()

    def test_available_action_types_includes_something_else(self):
        """ It should still contain other valid keys """
        self.user_vals['printing_action'] = 'server'
        self.assertTrue(self.new_record())

    def test_onchange_printer_tray_id_empty(self):
        user = self.env['res.users'].new(
            {'printer_tray_id': False})
        user.onchange_printing_printer_id()
        self.assertFalse(user.printer_tray_id)

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

        user = self.env['res.users'].new(
            {'printer_tray_id': tray.id})
        self.assertEqual(user.printer_tray_id, tray)
        user.onchange_printing_printer_id()
        self.assertFalse(user.printer_tray_id)
