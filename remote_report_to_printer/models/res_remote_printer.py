# Copyright (c) 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResRemotePrinter(models.Model):
    _name = "res.remote.printer"
    _description = "Remote Printer"

    remote_id = fields.Many2one(
        "res.remote",
        ondelete="cascade",
        readonly=True,
    )
    printer_id = fields.Many2one(
        "printing.printer",
        ondelete="cascade",
    )
    printer_tray_id = fields.Many2one(
        "printing.tray",
        ondelete="cascade",
        domain="[('printer_id', '=', printer_id)]",
    )
    is_default = fields.Boolean(default=False)
    printer_usage = fields.Selection([("standard", "Standard")], default="standard")

    _sql_constraints = [
        (
            "unique_printer_remote_usage",
            "unique(remote_id,printer_id,printer_usage)",
            "A Remote cannot have the same printer for the same usage",
        )
    ]

    @api.onchange("printer_id")
    def _onchange_printing_printer_id(self):
        """Reset the tray when the printer is changed"""
        self.printer_tray_id = False

    @api.constrains("remote_id", "printer_usage", "is_default")
    def _check_remote_usage(self):
        for rec in self.filtered(lambda r: r.is_default):
            if rec.remote_id.remote_printer_ids.filtered(
                lambda r: r != rec
                and r.is_default
                and r.printer_usage == rec.printer_usage
            ):
                raise ValidationError(_("Only one default printer is allowed"))
