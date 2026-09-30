from odoo import fields, models


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    zpl_printer_id = fields.Many2one("zpl_printer.zpl_printer", "Label Printer")
