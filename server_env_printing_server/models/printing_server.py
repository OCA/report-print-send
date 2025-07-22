# Copyright (C) 2021 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PrintingServer(models.Model):
    _name = "printing.server"
    _inherit = ["printing.server", "server.env.mixin"]

    @property
    def _server_env_fields(self):
        base_fields = super()._server_env_fields
        base_fields.update(
            {
                "address": {},
                "port": {},
                "user": {},
                "password": {},
            }
        )
        return base_fields
