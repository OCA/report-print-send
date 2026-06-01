from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    zpl_printer_id = fields.Many2one("zpl_printer.zpl_printer", "Label Printer")
    label_qty = fields.Integer(
        "Label Quantity", default=1, help="Amount of labels to be printed for each unit"
    )
