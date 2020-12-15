# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.tests.common import TransactionCase


class TestIrActionsReportXml(TransactionCase):

    def setUp(self):
        super(TestIrActionsReportXml, self).setUp()
        self.Model = self.env['ir.actions.report']
        self.vals = {}

        self.report = self.env['ir.actions.report'].search([], limit=1)
        self.server = self.env['printing.server'].create({})

    def new_action(self):
        return self.env['printing.action'].create({
            'name': 'Printing Action',
            'action_type': 'server',
        })

    def new_printing_action(self):
        return self.env['printing.report.xml.action'].create({
            'report_id': self.report.id,
            'user_id': self.env.ref('base.user_demo').id,
            'action': 'server',
        })

    def new_printer(self):
        return self.env['printing.printer'].create({
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

    def test_print_action_for_report_name_gets_report(self):
        """ It should get report by name """
        with mock.patch.object(self.Model, '_get_report_from_name') as mk:
            expect = 'test'
            self.Model.print_action_for_report_name(expect)
            mk.assert_called_once_with(
                expect
            )

    def test_print_action_for_report_name_returns_if_no_report(self):
        """ It should return empty dict when no matching report """
        with mock.patch.object(self.Model, '_get_report_from_name') as mk:
            expect = 'test'
            mk.return_value = False
            res = self.Model.print_action_for_report_name(expect)
            self.assertDictEqual(
                {}, res,
            )

    def test_print_action_for_report_name_returns_if_report(self):
        """ It should return correct serializable result for behaviour """
        with mock.patch.object(self.Model, '_get_report_from_name') as mk:
            res = self.Model.print_action_for_report_name('test')
            behaviour = mk().behaviour()[mk()]
            expect = {
                'action': behaviour['action'],
                'printer_name': behaviour['printer'].name,
            }
            self.assertDictEqual(
                expect, res,
                'Expect %s, Got %s' % (expect, res),
            )

    def test_behaviour_default_values(self):
        """ It should return the default action and printer """
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = False
        self.env.user.printing_printer_id = False
        report.property_printing_action_id = False
        report.printing_printer_id = False
        self.assertEqual(report.behaviour(), {
            report: {
                'action': 'client',
                'printer': self.env['printing.printer'],
            },
        })

    def test_behaviour_user_values(self):
        """ It should return the action and printer from user """
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = 'client'
        self.env.user.printing_printer_id = self.new_printer()
        self.assertEqual(report.behaviour(), {
            report: {
                'action': 'client',
                'printer': self.env.user.printing_printer_id,
            },
        })

    def test_behaviour_report_values(self):
        """ It should return the action and printer from report """
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = 'client'
        report.property_printing_action_id = self.new_action()
        report.printing_printer_id = self.new_printer()
        self.assertEqual(report.behaviour(), {
            report: {
                'action': report.property_printing_action_id.action_type,
                'printer': report.printing_printer_id,
            },
        })

    def test_behaviour_user_action(self):
        """ It should return the action and printer from user action"""
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = 'client'
        report.property_printing_action_id.action_type = 'user_default'
        self.assertEqual(report.behaviour(), {
            report: {
                'action': 'client',
                'printer': report.printing_printer_id,
            },
        })

    def test_behaviour_printing_action_on_wrong_user(self):
        """ It should return the action and printer ignoring printing action
        """
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = 'client'
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env['res.users'].search([
            ('id', '!=', self.env.user.id),
        ], limit=1)
        self.assertEqual(report.behaviour(), {
            report: {
                'action': 'client',
                'printer': report.printing_printer_id,
            },
        })

    def test_behaviour_printing_action_on_wrong_report(self):
        """ It should return the action and printer ignoring printing action
        """
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = 'client'
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env.user
        printing_action.report_id = self.env['ir.actions.report'].search([
            ('id', '!=', report.id),
        ], limit=1)
        self.assertEqual(report.behaviour(), {
            report: {
                'action': 'client',
                'printer': report.printing_printer_id,
            },
        })

    def test_behaviour_printing_action_with_no_printer(self):
        """ It should return the action from printing action and printer from other
        """
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = 'client'
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env.user
        printing_action.report_id = report
        self.assertEqual(report.behaviour(), {
            report: {
                'action': printing_action.action,
                'printer': report.printing_printer_id,
            },
        })

    def test_behaviour_printing_action_with_printer(self):
        """ It should return the action and printer from printing action """
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = 'client'
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env.user
        printing_action.printer_id = self.new_printer()
        self.assertEqual(report.behaviour(), {
            report: {
                'action': printing_action.action,
                'printer': printing_action.printer_id,
            },
        })

    def test_behaviour_printing_action_user_defaults(self):
        """ It should return the action and printer from user with printing action
        """
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = 'client'
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env.user
        printing_action.action = 'user_default'
        self.assertEqual(report.behaviour(), {
            report: {
                'action': 'client',
                'printer': report.printing_printer_id,
            },
        })

    def test_onchange_printer_tray_id_empty(self):
        action = self.env['ir.actions.report'].new(
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

        action = self.env['ir.actions.report'].new(
            {'printer_tray_id': tray.id})
        self.assertEqual(action.printer_tray_id, tray)
        action.onchange_printing_printer_id()
        self.assertFalse(action.printer_tray_id)
