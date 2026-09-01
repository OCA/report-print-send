# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os
from base64 import b64encode

from odoo import fields, models

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

    def print_file(self, file_name, report=None, **print_opts):
        if self.backend != "websocket":
            return super().print_file(file_name, report=report, **print_opts)
        self.ensure_one()
        with open(file_name, "rb") as f:
            content = f.read()
        pdf_b64 = b64encode(content).decode("utf-8")
        payload = {
            "printer_name": self.system_name or "",
            "file_data": pdf_b64,
            "file_type": print_opts.get("doc_format", "qweb-pdf"),
        }
        self.env["bus.bus"]._sendone(self, "print_job", payload)
        try:
            os.remove(file_name)
        except OSError as exc:
            _logger.warning("Unable to remove temporary file %s: %s", file_name, exc)
        _logger.debug("Print job sent via WebSocket to printer '%s'", self.name)
        return True
