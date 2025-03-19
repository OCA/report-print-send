# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = ["res.company", "server.env.techname.mixin"]

    @property
    def _server_env_fields(self):
        base_fields = super()._server_env_fields
        pingen_fields = {
            "pingen_clientid": {},
            "pingen_client_secretid": {},
            "pingen_organization": {},
            "pingen_staging": {},
            "pingen_webhook_secret": {},
        }
        pingen_fields.update(base_fields)
        return pingen_fields
