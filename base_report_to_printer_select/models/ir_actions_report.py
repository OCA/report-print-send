# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _get_select_paperformat(self):
        """Paper format the candidate printers must support. A text report
        (labels) never falls back to the company format: without one of its
        own, any printer qualifies."""
        self.ensure_one()
        if self.report_type == "qweb-text":
            return self.paperformat_id
        return self.get_paperformat()

    def _get_candidate_printers_domain(self):
        self.ensure_one()
        paperformat = self._get_select_paperformat()
        if not paperformat:
            return []
        return [
            "|",
            ("paperformat_ids", "=", False),
            ("paperformat_ids", "in", paperformat.ids),
        ]

    def _get_candidate_printers(self):
        """Printers the user may choose from when printing this report"""
        return self.env["printing.printer"].search(
            self._get_candidate_printers_domain()
        )

    def _get_other_printers(self):
        """The remaining active printers, offered behind "See more" """
        return self.env["printing.printer"].search([]) - self._get_candidate_printers()

    def behaviour(self, **extras):
        result = super().behaviour(**extras)
        if result.get("action") == "select":
            result.pop("printer_exception", None)
        return result

    @api.model
    def print_action_for_report_name(self, report_name):
        result = super().print_action_for_report_name(report_name)
        if result.get("action") != "select":
            return result
        report = self._get_report_from_name(report_name)
        printers = report._get_candidate_printers()
        preselected = report.behaviour().get("printer")
        result.pop("printer_exception", None)
        result["printers"] = [
            {
                "id": printer.id,
                "name": printer.name,
                "backend": printer.backend,
                "status": printer.status,
            }
            for printer in printers
        ]
        result["printer_id"] = preselected.id if preselected in printers else False
        result["other_printers"] = [
            {
                "id": printer.id,
                "name": printer.name,
                "backend": printer.backend,
                "status": printer.status,
            }
            for printer in report._get_other_printers()
        ]
        return result

    def print_document_select(self, record_ids, printer_id, data=None):
        """Print on the printer the user picked and remember the choice"""
        self.ensure_one()
        self.env[self.sudo().model].browse(record_ids).check_access("read")
        report = self.sudo()
        printer = self.env["printing.printer"].browse(printer_id).exists()
        if not printer or not printer.active:
            raise exceptions.UserError(_("The selected printer is not available."))
        report._remember_selected_printer(printer)
        return report.print_document_client_action(
            record_ids, data=data, printer=printer.id
        )

    def _remember_selected_printer(self, printer):
        action_obj = self.env["printing.report.xml.action"].sudo()
        line = action_obj.search(
            [("report_id", "=", self.id), ("user_id", "=", self.env.uid)], limit=1
        )
        if line and line.action != "select":
            return
        values = {
            "printer_id": printer.id,
            "printer_input_tray_id": False,
            "printer_output_tray_id": False,
        }
        if line:
            line.write(values)
        else:
            action_obj.create(
                dict(values, report_id=self.id, user_id=self.env.uid, action="select")
            )
