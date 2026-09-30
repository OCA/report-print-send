# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class IrWebsocket(models.AbstractModel):
    _inherit = "ir.websocket"

    def _build_bus_channel_list(self, channels):
        websocket_printers = (
            self.env["printing.printer"]
            .sudo()
            .search(
                [
                    ("backend", "=", "websocket"),
                    ("websocket_user_id", "=", self.env.uid),
                ]
            )
        )
        for printer in websocket_printers:
            channels.append(printer)
        return super()._build_bus_channel_list(channels)
