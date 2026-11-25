from odoo import fields, models


class PrintingPrinter(models.Model):
    _inherit = "printing.printer"

    backend = fields.Selection(
        selection_add=[("qztray", "QZTray")],
        ondelete={"qztray": "cascade"},
    )
