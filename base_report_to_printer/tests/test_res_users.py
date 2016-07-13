# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class TestResUsers(TransactionCase):

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
