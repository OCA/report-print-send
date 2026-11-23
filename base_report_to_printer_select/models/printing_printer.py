# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PrintingPrinter(models.Model):
    _inherit = "printing.printer"

    paperformat_ids = fields.Many2many(
        comodel_name="report.paperformat",
        string="Paper formats",
        help="Paper formats this printer can print. When a report asks the "
        "user to select a printer, only the printers supporting its paper "
        "format are offered. Leave empty to accept any report.",
    )
