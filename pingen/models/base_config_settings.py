# Copyright 2012-2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pingen_clientid = fields.Char(
        string="Pingen Client ID", related="company_id.pingen_clientid", readonly=False
    )
    pingen_client_secretid = fields.Char(
        string="Pingen Client Secret ID",
        related="company_id.pingen_client_secretid",
        readonly=False,
    )
    pingen_organization = fields.Char(
        string="Pingen organization",
        related="company_id.pingen_organization",
        readonly=False,
    )
    pingen_webhook_secret = fields.Char(
        string="Pingen webhook secret",
        related="company_id.pingen_webhook_secret",
        readonly=False,
    )
    pingen_staging = fields.Boolean(
        string="Pingen Staging", related="company_id.pingen_staging", readonly=False
    )
