# Copyright (C) 2022 PESOL (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PrintingReportQzTray(models.Model):
    _name = "printing.report.qz.tray"
    _description = "Printing Report Qz Tray"

    report_id = fields.Many2one(
        comodel_name="ir.actions.report",
        string="Report",
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users", string="User", required=True, ondelete="cascade"
    )
    action = fields.Selection(
        [("print", "Print"), ("download", "Download")], string="Action"
    )
    # TODO: Use js to show local printers and select one
    qz_tray_printer = fields.Char(string="QZ Tray Printer")
