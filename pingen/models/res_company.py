# Author: Guewen Baconnier
# Copyright 2012-2023 Camptocamp SA
# Copyright 2026 Altixia LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from .pingen import Pingen


class ResCompany(models.Model):
    _inherit = "res.company"

    # Credentials: readable by administrators only (res.company is readable
    # by every internal user).
    pingen_clientid = fields.Char(size=20, groups="base.group_system")
    pingen_client_secretid = fields.Char(size=80, groups="base.group_system")
    pingen_organization = fields.Char("Pingen organization ID")
    pingen_webhook_secret = fields.Char(groups="base.group_system")
    pingen_staging = fields.Boolean()
    pingen_ssl_verify = fields.Boolean(default=True)
    pingen_address_position = fields.Selection(
        [("left", "Left"), ("right", "Right")],
        string="Pingen address position",
        default="left",
        help="Envelope window where the recipient address is printed on the "
        "first page of the documents sent to Pingen.",
    )

    def _pingen(self):
        """Return a Pingen instance to work on"""
        self.ensure_one()
        # Credentials are restricted to administrators; the crons and the
        # document actions of regular users still need them.
        company = self.sudo()
        return Pingen(
            company.pingen_clientid,
            company.pingen_client_secretid,
            organization=company.pingen_organization,
            staging=company.pingen_staging,
            verify=company.pingen_ssl_verify,
            address_position=company.pingen_address_position,
        )

    def _get_pingen_client(self):
        """Returns a pingen session for a user"""
        return self._pingen()
