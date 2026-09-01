# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.base_report_to_printer_raw.models.printing_printer import (
    RAW_TEST_ZPL,
)


class TestPrintingPrinterRaw(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Model = self.env["printing.printer"]
        self.printer_vals = {
            "name": "Zebra Raw",
            "system_name": "zebra-raw",
            "backend": "raw",
            "raw_host": "192.168.1.50",
            "raw_port": 9100,
            "status": "unknown",
        }

    def new_record(self, **extra):
        vals = dict(self.printer_vals, **extra)
        return self.Model.create(vals)

    def test_send_raw_payload_encodes_strings(self):
        printer = self.new_record()
        with mock.patch("socket.socket") as mock_socket_cls:
            mock_sock = mock_socket_cls.return_value.__enter__.return_value
            printer._send_raw_payload("^XA^XZ")
            mock_sock.connect.assert_called_once_with(("192.168.1.50", 9100))
            mock_sock.sendall.assert_called_once_with(b"^XA^XZ")

    def test_send_raw_payload_missing_host_raises(self):
        printer = self.new_record(raw_host=False)
        with self.assertRaises(UserError):
            printer._send_raw_payload(b"^XA^XZ")

    def test_print_file_sends_file_bytes(self):
        printer = self.new_record()
        with mock.patch.object(type(printer), "_send_raw_payload") as send:
            with open(__file__, "rb") as handle:
                path = handle.name
            printer.print_file(path)
            send.assert_called_once()
            payload = send.call_args[0][0]
            self.assertIsInstance(payload, bytes)
            self.assertTrue(payload)

    def test_print_file_non_raw_delegates_to_super(self):
        printer = self.new_record(backend="base")
        with mock.patch.object(type(printer), "_send_raw_payload") as send:
            printer.print_file(__file__)
            send.assert_not_called()

    def test_print_file_socket_error_raises_user_error(self):
        printer = self.new_record()
        with mock.patch.object(
            type(printer),
            "_send_raw_payload",
            side_effect=OSError("Connection refused"),
        ):
            with self.assertRaises(UserError):
                printer.print_file(__file__)

    def test_print_test_page_sends_zpl(self):
        printer = self.new_record()
        with mock.patch.object(type(printer), "_send_raw_payload") as send:
            printer.print_test_page()
            send.assert_called_once_with(RAW_TEST_ZPL)

    def test_invalid_raw_port_raises(self):
        with self.assertRaises(ValidationError):
            self.new_record(raw_port=0)

    def test_print_document_end_to_end(self):
        printer = self.new_record()
        zpl = "^XA^FO10,10^FDHello^FS^XZ"
        with mock.patch("socket.socket") as mock_socket_cls:
            mock_sock = mock_socket_cls.return_value.__enter__.return_value
            printer.print_document(report=None, content=zpl, doc_format="raw")
            mock_sock.sendall.assert_called_once_with(zpl.encode("utf-8"))

    @mock.patch("cups.Connection")
    def test_raw_printer_does_not_use_cups(self, cups_conn_mock):
        """Raw and CUPS backends can coexist: raw jobs must not touch CUPS."""
        printer = self.new_record()
        with mock.patch.object(type(printer), "_send_raw_payload"):
            printer.print_file(__file__)
        cups_conn_mock.assert_not_called()
