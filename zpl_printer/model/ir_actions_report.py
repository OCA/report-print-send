from odoo import fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(
        selection_add=[("qweb-zpl", "qweb-zpl")],
        ondelete={
            "qweb-zpl": "cascade",
        },
    )

    def render_zpl(self, report_ref, docids, data=None):
        return self._render_qweb_text(report_ref, docids, data)
