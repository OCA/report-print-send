# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import socket

from odoo import api, exceptions, fields, models

_logger = logging.getLogger(__name__)

DEFAULT_RAW_PORT = 9100
DEFAULT_RAW_TIMEOUT = 5.0
RAW_TEST_ZPL = b"^XA^FO50,50^ADN,36,20^FDTEST^FS^XZ"


class PrintingPrinter(models.Model):
    _inherit = "printing.printer"

    backend = fields.Selection(
        selection_add=[("raw", "Raw Socket")],
        ondelete={"raw": "cascade"},
    )
    raw_host = fields.Char(
        string="Host",
        help="IP address or hostname of the network printer.",
    )
    raw_port = fields.Integer(
        string="Port",
        default=DEFAULT_RAW_PORT,
        help="TCP port for raw printing (typically 9100 for ZPL printers).",
    )
    raw_timeout = fields.Float(
        string="Timeout (seconds)",
        default=DEFAULT_RAW_TIMEOUT,
        help="Socket connection and send timeout.",
    )

    @api.constrains("backend", "raw_port")
    def _check_raw_port(self):
        for printer in self:
            if printer.backend != "raw":
                continue
            if not printer.raw_port or printer.raw_port < 1 or printer.raw_port > 65535:
                raise exceptions.ValidationError(
                    self.env._("Raw socket port must be between 1 and 65535.")
                )

    def _send_raw_payload(self, payload):
        """Transmit raw bytes to the printer over a TCP socket."""
        self.ensure_one()
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        host = (self.raw_host or "").strip()
        if not host:
            raise exceptions.UserError(
                self.env._(
                    "Printer %(printer)s has no host configured for raw printing.",
                    printer=self.display_name,
                )
            )
        port = self.raw_port or DEFAULT_RAW_PORT
        timeout = self.raw_timeout or DEFAULT_RAW_TIMEOUT
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.sendall(payload)
        _logger.info("Raw print job sent to %s:%s (%d bytes)", host, port, len(payload))

    def print_file(self, file_name, report=None, **print_opts):
        self.ensure_one()
        if self.backend != "raw":
            return super().print_file(file_name, report=report, **print_opts)
        with open(file_name, "rb") as handle:
            payload = handle.read()
        try:
            self._send_raw_payload(payload)
        except OSError as err:
            raise exceptions.UserError(
                self.env._(
                    "Failed to send raw print job to %(host)s:%(port)s: %(error)s",
                    host=self.raw_host,
                    port=self.raw_port or DEFAULT_RAW_PORT,
                    error=err,
                )
            ) from err
        return True

    def print_test_page(self):
        raw_printers = self.filtered(lambda p: p.backend == "raw")
        for printer in raw_printers:
            try:
                printer._send_raw_payload(RAW_TEST_ZPL)
            except OSError as err:
                raise exceptions.UserError(
                    self.env._(
                        "Failed to print test page on printer %(printer)s: %(error)s",
                        printer=printer.display_name,
                        error=err,
                    )
                ) from err
        return super(PrintingPrinter, self - raw_printers).print_test_page()
