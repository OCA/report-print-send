# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PrinterTray(models.Model):
    _name = "printing.tray"
    _description = "Printer Tray"

    _order = "name asc"

    name = fields.Char(required=True)
    system_name = fields.Char(required=True, readonly=True)
    printer_id = fields.Many2one(
        comodel_name="printing.printer",
        string="Printer",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
