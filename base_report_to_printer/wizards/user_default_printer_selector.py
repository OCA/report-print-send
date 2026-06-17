# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WizStockBarcodesUserPrinterSelector(models.TransientModel):
    _name = "wiz.user.default.printer.selector"
    _description = "Wizard to select user printer"

    printing_printer_id = fields.Many2one(
        comodel_name="printing.printer",
        string="Default Printer",
        default=lambda self: self.env.user.printing_printer_id,
    )

    def action_confirm(self):
        self.ensure_one()
        self.env.user.printing_printer_id = self.printing_printer_id
