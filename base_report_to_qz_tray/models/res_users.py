# Copyright (C) 2022 PESOL (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    report_default_action = fields.Selection(
        [("print", "Print"), ("download", "Download")],
        default="download",
        string="Report Action",
    )
    # TODO: Use js to show local printers and select one
    qz_tray_printer = fields.Char(string="QZ Tray Printer")

    printing_report_qz_tray_ids = fields.One2many(
        comodel_name="printing.report.qz.tray",
        inverse_name="user_id",
        string="Default Report Actions",
        help="This field allows configuring action and printer on a per " "user basis",
    )
