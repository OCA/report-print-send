# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    printing_group_ids = fields.Many2many(
        comodel_name="printing.group",
        relation="printing_group_res_users_rel",
        column1="user_id",
        column2="group_id",
        string="Printing Groups",
    )
