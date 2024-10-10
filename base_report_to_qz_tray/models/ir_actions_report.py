# Copyright (C) 2022 PESOL (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import api, fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    printing_report_qz_tray_ids = fields.One2many(
        comodel_name="printing.report.qz.tray",
        inverse_name="report_id",
        string="Default Actions",
        help="This field allows configuring action and printer on a per " "user basis",
    )

    @api.model
    def qz_tray_for_report_name(self, report_name):
        """Returns if the action is a direct print or pdf

        Called from js
        """
        report = self._get_report_from_name(report_name)

        if not report or self.env.context.get("must_skip_send_to_printer"):
            return {"action": "download", "printer_name": self.env.user.qz_tray_printer}

        # get values for specific report and user
        report_action_values = report.get_default_report_action(user_id=self.env.uid)
        if report_action_values:
            return report_action_values

        # get values for specific report, for all users
        report_action_values = report.get_default_report_action()
        if report_action_values:
            return report_action_values

        # get values for user or download
        return {
            "id": report.id,
            "action": self.env.user.report_default_action or "download",
            "printer_name": self.env.user.qz_tray_printer or False,
        }

    def get_default_report_action(self, user_id=False):
        self.ensure_one()
        printing_act_obj = self.env["printing.report.qz.tray"]
        printing_report_qz_tray = printing_act_obj.search(
            # [
            #     ("report_id", "=", self.id),
            #     ("user_id", "=", user_id),
            # ],
            [
                ("report_id", "=", self.id),
                "|",
                ("user_id", "=", user_id),
                ("user_id", "=", False),
            ],
            limit=1,
        )
        if not printing_report_qz_tray:
            return False
        return {
            "id": self.id,
            "action": printing_report_qz_tray.action,
            "printer_name": printing_report_qz_tray.qz_tray_printer,
        }

    def get_qz_tray_data(self, res_ids, report_type="pdf", report_name="", data=None):
        if report_type == "pdf":
            # Pre V16
            # result = self._render_qweb_pdf(res_ids, data)
            # Post V16
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
            # Pre V16
            # result = self._render_qweb_text(res_ids, data)
            # Post V16
            result = self.env["ir.actions.report"]._render_qweb_text(
                report_name, res_ids, data
            )
            data = [result[0].replace(b"\n", b"").decode("unicode_escape")]
        else:
            data = []
        return data
