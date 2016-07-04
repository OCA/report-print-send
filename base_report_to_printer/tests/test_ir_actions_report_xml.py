# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.tests.common import TransactionCase


class TestIrActionsReportXml(TransactionCase):

    def setUp(self):
        super(TestIrActionsReportXml, self).setUp()
        self.Model = self.env['ir.actions.report.xml']
        self.vals = {}

    def new_record(self):
        return self.Model.create(self.vals)

    def test_print_action_for_report_name_gets_report(self):
        """ It should get report by name """
        with mock.patch.object(self.Model, 'env') as mk:
            expect = 'test'
            self.Model.print_action_for_report_name(expect)
            mk['report']._get_report_from_name.assert_called_once_with(
                expect
            )

    def test_print_action_for_report_name_returns_if_no_report(self):
        """ It should return empty dict when no matching report """
        with mock.patch.object(self.Model, 'env') as mk:
            expect = 'test'
            mk['report']._get_report_from_name.return_value = False
            res = self.Model.print_action_for_report_name(expect)
            self.assertDictEqual(
                {}, res,
            )

    def test_print_action_for_report_name_returns_if_report(self):
        """ It should return correct serializable result for behaviour """
        with mock.patch.object(self.Model, 'env') as mk:
            res = self.Model.print_action_for_report_name('test')
            behaviour = mk['report']._get_report_from_name().behaviour()[
                mk['report']._get_report_from_name().id
            ]
            expect = {
                'action': behaviour['action'],
                'printer_name': behaviour['printer'].name,
            }
            self.assertDictEqual(
                expect, res,
                'Expect %s, Got %s' % (expect, res),
            )
