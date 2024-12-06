# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PrintingAutoTesterChild(models.Model):
    _name = "printingauto.tester.child"

    name = fields.Char()


class PrintingAutoTester(models.Model):
    _name = "printingauto.tester"
    _inherit = "printing.auto.mixin"

    name = fields.Char()
    child_ids = fields.Many2many("printingauto.tester.child")
