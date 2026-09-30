from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    printer_selection_strategy = fields.Selection(
        [
            ("always_user_default", "Always User Default"),
            ("product_before_user", "Use product printer, otherwise user printer"),
        ],
        default="product_before_user",
    )
    zpl_printer_id = fields.Many2one("zpl_printer.zpl_printer", "Default Label Printer")

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            "printer_selection_strategy",
            "zpl_printer_id",
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + [
            "printer_selection_strategy",
            "zpl_printer_id",
        ]
