# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PrintRecordEscpos(models.TransientModel):

    _name = "print.record.escpos"
    _description = "Wizard for printing escpos tickets"

    printer_id = fields.Many2one(
        comodel_name="printing.printer",
        string="Printer",
        required=True,
        help="Printer used to print the labels.",
    )
    escpos_id = fields.Many2one(
        comodel_name="printing.escpos",
        string="Label",
        required=True,
        domain=lambda self: [
            ("model_id.model", "=", self.env.context.get("active_model"))
        ],
        help="Label to print.",
    )
    active_model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Model",
        domain=lambda self: [("model", "=", self.env.context.get("active_model"))],
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        # Automatically select the printer and label, if only one is available
        printers = self.env["printing.printer"].search(
            [("id", "=", self.env.context.get("printer_escpos_id"))]
        )
        if not printers:
            printers = self.env["printing.printer"].search([])
        if len(printers) == 1:
            values["printer_id"] = printers.id

        escpos = self.env["printing.escpos"].search(
            [("model_id.model", "=", self.env.context.get("active_model"))]
        )
        if len(escpos) == 1:
            values["escpos_id"] = escpos.id

        return values

    def print_escpos(self):
        """Prints a label per selected record"""
        record_model = self.env.context["active_model"]
        for record_id in self.env.context["active_ids"]:
            record = self.env[record_model].browse(record_id)
            self.escpos_id.print_escpos(self.printer_id, record)
