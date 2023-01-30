# Author: Guewen Baconnier
# Copyright 2012-2017 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from .pingen import Pingen


class ResCompany(models.Model):

    _inherit = "res.company"

    pingen_clientid = fields.Char("Pingen Client ID", size=20)
    pingen_client_secretid = fields.Char("Pingen Client Secret ID", size=80)
    pingen_organization = fields.Char("Pingen organization ID")
    pingen_webhook_secret = fields.Char("Pingen Webhooks secret")
    pingen_staging = fields.Boolean("Pingen Staging")

    def _pingen(self):
        """Return a Pingen instance to work on"""
        self.ensure_one()

        clientid = self.pingen_clientid
        secretid = self.pingen_client_secretid
        return Pingen(
            clientid,
            secretid,
            organization=self.pingen_organization,
            staging=self.pingen_staging,
        )

    def _get_pingen_client(self):
        """Returns a pingen session for a user"""
        return self._pingen()
