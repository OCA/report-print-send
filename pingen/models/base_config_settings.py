# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BaseConfigSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    pingen_clientid = fields.Char(related='company_id.pingen_clientid')
    pingen_client_secretid = fields.Char(related='company_id.pingen_client_secretid')
    pingen_staging_clientid = fields.Char(related='company_id.pingen_staging_clientid')
    pingen_staging_client_secretid = fields.Char(related='company_id.pingen_staging_client_secretid')
    pingen_organization = fields.Char(related='company_id.pingen_organization')
    pingen_staging = fields.Boolean(related='company_id.pingen_staging')
