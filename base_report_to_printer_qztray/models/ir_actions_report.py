# Copyright (C) 2022 PESOL (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def get_qz_tray_data(self, res_ids, report_type="pdf", report_name="", data=None):
        if report_type == "pdf":
            result = self.env["ir.actions.report"]._render_qweb_pdf(
                report_name, res_ids, data
            )
            data = [
                {
                    "type": "pixel",
                    "format": "pdf",
                    "flavor": "base64",
                    "data": base64.b64encode(result[0]),
                }
            ]
        elif report_type == "text":
            result = self.env["ir.actions.report"]._render_qweb_text(
                report_name, res_ids, data
            )
            data = [result[0].replace(b"\n", b"").decode("unicode_escape")]
        else:
            data = []
        return data
