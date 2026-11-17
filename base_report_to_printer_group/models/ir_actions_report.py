# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv import expression


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _get_print_action(self):
        print_action = super()._get_print_action()
        if print_action:
            return print_action
        return self.env["printing.report.xml.action"].search(
            [
                ("report_id", "=", self.id),
                ("group_id", "in", self.env.user.printing_group_ids.ids),
                ("action", "!=", "user_default"),
            ],
            order="group_id, id",
            limit=1,
        )

    def _get_candidate_printers_domain(self):
        domain = super()._get_candidate_printers_domain()
        printers = self.env.user.printing_group_ids.printer_ids
        if printers:
            domain = expression.AND([domain, [("id", "in", printers.ids)]])
        return domain
