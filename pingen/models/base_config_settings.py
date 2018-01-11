# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BaseConfigSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    pingen_token = fields.Char(related='company_id.pingen_token')
    pingen_staging = fields.Boolean(related='company_id.pingen_staging')
