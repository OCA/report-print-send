# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models

PRINTER_EXCEPTION_STATUSES = ("error", "server-error", "unavailable")


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def behaviour(self):
        """A WebSocket printer has no CUPS server to reach, so the connection
        check of the base module would always flag it: only its status can."""
        result = super().behaviour()
        printer = result.get("printer")
        if printer and printer.backend == "websocket":
            result.pop("printer_exception", None)
            if (
                printer.status in PRINTER_EXCEPTION_STATUSES
                and not self.env.context.get("skip_printer_exception")
            ):
                result["printer_exception"] = True
        return result

    @api.model
    def print_action_for_report_name(self, report_name):
        result = super().print_action_for_report_name(report_name)
        if result:
            report = self._get_report_from_name(report_name)
            result["backend"] = report.behaviour()["printer"].backend
        return result
