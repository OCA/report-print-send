# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class StopTest(Exception):
    pass


class TestReport(TransactionCase):

    def setUp(self):
        super(TestReport, self).setUp()
        self.Model = self.env['report']
        self.report_vals = {}

    def new_record(self):
        return self.Model.create(self.report_vals)

    def test_can_print_report_context_skip(self):
        """ It should return False based on context """
        rec_id = self.new_record().with_context(
            must_skip_send_to_printer=True
        )
        res = rec_id._can_print_report(
            {'action': 'server'}, True, True
        )
        self.assertFalse(res)

    def test_can_print_report_true(self):
        """ It should return True when server print allowed """
        res = self.new_record()._can_print_report(
            {'action': 'server'}, True, True
        )
        self.assertTrue(res)

    def test_can_print_report_false(self):
        """ It should return False when server print not allowed """
        res = self.new_record()._can_print_report(
            {'action': 'server'}, True, False
        )
        self.assertFalse(res)
