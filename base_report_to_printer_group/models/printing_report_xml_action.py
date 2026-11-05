# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class PrintingReportXmlAction(models.Model):
    _inherit = "printing.report.xml.action"

    user_id = fields.Many2one(required=False)
    group_id = fields.Many2one(
        comodel_name="printing.group", string="Printing Group", ondelete="cascade"
    )

    @api.constrains("report_id", "user_id", "group_id")
    def _check_user_or_group(self):
        for action in self:
            if bool(action.user_id) == bool(action.group_id):
                raise exceptions.ValidationError(
                    _("A specific printing action needs either a user or a group.")
                )
