# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os
from base64 import b64encode

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PrintingPrinter(models.Model):
    _inherit = "printing.printer"

    backend = fields.Selection(
        selection_add=[("websocket", "WebSocket")],
        ondelete={"websocket": "cascade"},
    )
    websocket_user_id = fields.Many2one(
        "res.users",
    )

    @api.onchange("backend")
    def _onchange_backend_websocket(self):
        if self.backend == "websocket":
            self.server_id = False

    def print_document(self, report, content, **print_opts):
        """Return the printing job, created in this transaction: the file
        itself is sent after the commit."""
        if self.backend != "websocket":
            return super().print_document(report, content, **print_opts)
        self.ensure_one()
        job = self.env["printing.job"]._websocket_create(
            self, print_opts.get("title") or (report and report.name) or self.name
        )
        super().print_document(report, content, websocket_job_id=job.id, **print_opts)
        return job

    def print_file(self, file_name, report=None, **print_opts):
        if self.backend != "websocket":
            return super().print_file(file_name, report=report, **print_opts)
        self.ensure_one()
        with open(file_name, "rb") as f:
            content = f.read()
        pdf_b64 = b64encode(content).decode("utf-8")
        job = self.env["printing.job"].sudo().browse(
            print_opts.get("websocket_job_id")
        ).exists() or self.env["printing.job"]._websocket_create(
            self, print_opts.get("title") or (report and report.name) or self.name
        )
        payload = {
            "printer_name": self.system_name or "",
            "file_data": pdf_b64,
            "file_type": print_opts.get("doc_format", "qweb-pdf"),
            "job_uuid": job.websocket_uuid,
        }
        self.env["bus.bus"]._sendone(self, "print_job", payload)
        try:
            os.remove(file_name)
        except OSError as exc:
            _logger.warning("Unable to remove temporary file %s: %s", file_name, exc)
        _logger.debug("Print job sent via WebSocket to printer '%s'", self.name)
        return job
