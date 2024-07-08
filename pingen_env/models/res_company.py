# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models

from odoo.addons.server_environment import serv_config


class ResCompany(models.Model):
    _inherit = ["res.company"]

    pingen_clientid = fields.Char(
        compute="_compute_pingen_env", required=False, readonly=True
    )
    pingen_client_secretid = fields.Char(
        compute="_compute_pingen_env", required=False, readonly=True
    )
    pingen_organization = fields.Char(
        compute="_compute_pingen_env", required=False, readonly=True
    )
    pingen_staging = fields.Boolean(
        compute="_compute_pingen_env", required=False, readonly=True
    )
    pingen_webhook_secret = fields.Char(
        compute="_compute_pingen_env", required=False, readonly=True
    )

    @api.depends()
    def _compute_pingen_env(self):
        global_section_name = "pingen"
        for company in self:
            # default vals
            config_vals = {
                "pingen_clientid": "",
                "pingen_client_secretid": "",
                "pingen_organization": "",
                "pingen_staging": True,
                "pingen_webhook_secret": "",
            }
            # TODO: using company name may be fragile, use tech name in the future instead
            if serv_config.has_section(global_section_name):
                config_vals.update(serv_config.items(global_section_name))
            custom_section_name = global_section_name + "." + company.name
            if serv_config.has_section(custom_section_name):
                config_vals.update(serv_config.items(custom_section_name))
            company.update(config_vals)
