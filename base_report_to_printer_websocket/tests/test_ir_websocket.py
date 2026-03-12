# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.tests.common import TransactionCase


class TestIrWebsocket(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ws_user = cls.env.ref("base.user_admin")
        cls.printer = cls.env["printing.printer"].create(
            {
                "name": "WS Printer",
                "system_name": "ws_printer",
                "backend": "websocket",
                "websocket_user_id": cls.ws_user.id,
            }
        )

    def _build_channel_list(self, user, channels):
        """Call _build_bus_channel_list and return the resulting channels."""
        mock_request = mock.MagicMock()
        mock_request.session.uid = user.id
        with mock.patch("odoo.addons.bus.models.ir_websocket.request", mock_request):
            IrWs = self.env["ir.websocket"].with_user(user)
            return IrWs._build_bus_channel_list(list(channels))

    def _get_printer_channels(self, user, channels=None):
        """Return only printing.printer records from the bus channel list."""
        result = self._build_channel_list(user, channels or [])
        return [
            ch
            for ch in result
            if hasattr(ch, "_name") and ch._name == "printing.printer"
        ]

    def test_assigned_user_gets_printer_channel(self):
        """The user assigned on the printer should receive its channel."""
        printer_channels = self._get_printer_channels(self.ws_user)
        self.assertIn(self.printer, printer_channels)

    def test_other_user_does_not_get_printer_channel(self):
        """A user not assigned on any printer should not receive printer channels."""
        other_user = self.env.ref("base.user_root")
        printer_channels = self._get_printer_channels(other_user)
        self.assertNotIn(self.printer, printer_channels)

    def test_multiple_printers_for_same_user(self):
        """A user assigned to multiple printers should receive all of them."""
        printer2 = self.env["printing.printer"].create(
            {
                "name": "WS Printer 2",
                "system_name": "ws_printer_2",
                "backend": "websocket",
                "websocket_user_id": self.ws_user.id,
            }
        )
        printer_channels = self._get_printer_channels(self.ws_user)
        self.assertIn(self.printer, printer_channels)
        self.assertIn(printer2, printer_channels)

    def test_non_websocket_printer_not_added(self):
        """Printers with a non-websocket backend should not be added."""
        self.env["printing.printer"].create(
            {
                "name": "CUPS Printer",
                "system_name": "cups_printer",
                "backend": "base",
            }
        )
        printer_channels = self._get_printer_channels(self.ws_user)
        self.assertEqual(len(printer_channels), 1)
        self.assertEqual(printer_channels[0], self.printer)
