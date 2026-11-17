# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PrintingAction(models.Model):
    _inherit = "printing.action"

    @property
    def _available_action_types(self):
        return super()._available_action_types + [("select", "Ask the user")]
