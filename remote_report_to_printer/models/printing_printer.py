# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PrintingPrinter(models.Model):

    _inherit = "printing.printer"

    printer_remote_ids = fields.One2many(
        "res.remote.printer",
        inverse_name="printer_id",
        string="Remotes",
        help="Remote that can use this printer.",
    )
