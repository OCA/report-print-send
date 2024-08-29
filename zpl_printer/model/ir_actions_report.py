from odoo import fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(
        selection_add=[("qweb-zpl", "qweb-zpl")],
        ondelete={
            "qweb-zpl": "cascade",
        },
    )
