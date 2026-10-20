# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PrintingGroup(models.Model):
    _name = "printing.group"
    _description = "Printing Group"
    _order = "sequence, name, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="printing_group_res_users_rel",
        column1="group_id",
        column2="user_id",
        string="Users",
    )
    printer_ids = fields.Many2many(
        comodel_name="printing.printer",
        string="Printers",
        help="Printers the users of this group may pick from when a report "
        "asks them to select a printer. Leave empty to offer any printer.",
    )
    printing_action_ids = fields.One2many(
        comodel_name="printing.report.xml.action",
        inverse_name="group_id",
        string="Report actions",
        help="Printing behaviour of the reports for the users of this group, "
        "unless they have their own specific action for the report.",
    )
