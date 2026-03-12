# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
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

    def print_document(
        self, report, content, action=None, doc_format="qweb-pdf", **kwargs
    ):
        if self.backend != "websocket":
            return super().print_document(
                report, content, action=action, doc_format=doc_format, **kwargs
            )
        self.ensure_one()
        if isinstance(content, str):
            content = content.encode("utf-8")
        pdf_b64 = b64encode(content).decode("utf-8")
        payload = {
            "printer_name": self.system_name or "",
            "file_data": pdf_b64,
            "file_type": doc_format,
        }
        self.env["bus.bus"]._sendone(self, "print_job", payload)
        _logger.debug("Print job sent via WebSocket to printer '%s'", self.name)
        return True
