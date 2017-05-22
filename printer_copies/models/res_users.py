# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    copies = fields.Integer(
        string='Copies',
        default=1
    )
