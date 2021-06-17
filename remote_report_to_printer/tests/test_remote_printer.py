# Copyright (c) 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestRemotePrinter(TransactionCase):
    def setUp(self):
        super().setUp()
        self.system_user_group = self.env.ref("base.group_system")
        self.user_group = self.env.ref("base.group_user")
        self.printer_manager = self._create_user(
            "printer_manager", self.system_user_group.id
        )
        self.printer_user = self._create_user("printer_user", self.user_group.id)

        name = "testing_remote_server"
        self.remote = self.env["res.remote"].search([("name", "=", name)])
        if not self.remote:
            self.remote = self.env["res.remote"].create(
                {"name": name, "ip": "127.0.0.1", "in_network": True}
            )
        self.server = self.env["printing.server"].create(
            {"name": "Server", "address": "localhost", "port": 631}
        )
        self.printer_1 = self.env["printing.printer"].create(
            {"name": "Printer 1", "system_name": "P1", "server_id": self.server.id}
        )
        self.printer_2 = self.env["printing.printer"].create(
            {"name": "Printer 2", "system_name": "P2", "server_id": self.server.id}
        )
        self.tray_1 = self.env["printing.tray"].create(
            {"name": "Tray", "system_name": "P2", "printer_id": self.printer_1.id}
        )

    def _create_user(self, name, group_ids):
        return (
            self.env["res.users"]
            .with_context({"no_reset_password": True})
            .create(
                {
                    "name": name,
                    "password": "demo",
                    "login": name,
                    "email": "@".join([name, "@test.com"]),
                    "groups_id": [(6, 0, [group_ids])],
                }
            )
        )

    def test_constrain(self):
        self.env["res.remote.printer"].with_user(self.printer_manager).create(
            {
                "remote_id": self.remote.id,
                "printer_id": self.printer_1.id,
                "is_default": True,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["res.remote.printer"].create(
                {
                    "remote_id": self.remote.id,
                    "printer_id": self.printer_2.id,
                    "is_default": True,
                }
            )

    def test_onchange_printer(self):
        remote_printer = (
            self.env["res.remote.printer"]
            .with_user(self.printer_manager)
            .create(
                {
                    "remote_id": self.remote.id,
                    "printer_id": self.printer_1.id,
                    "printer_tray_id": self.tray_1.id,
                }
            )
        )
        self.assertTrue(remote_printer.printer_tray_id)
        remote_printer.printer_id = self.printer_2
        remote_printer._onchange_printing_printer_id()
        self.assertFalse(remote_printer.printer_tray_id)

    def test_permissions_delete_manager(self):
        printer = (
            self.env["res.remote.printer"]
            .with_user(self.printer_manager)
            .create(
                {
                    "remote_id": self.remote.id,
                    "printer_id": self.printer_1.id,
                    "is_default": True,
                }
            )
        )
        printer.with_user(self.printer_manager).unlink()
        printer = self.env["res.remote.printer"].search(
            [
                ("remote_id", "=", self.remote.id),
                ("printer_id", "=", self.printer_1.id),
            ],
            limit=1,
        )
        self.assertEquals(printer, self.env["res.remote.printer"])

    def test_permissions_delete_user(self):
        printer = (
            self.env["res.remote.printer"]
            .with_user(self.printer_manager)
            .create(
                {
                    "remote_id": self.remote.id,
                    "printer_id": self.printer_1.id,
                    "is_default": True,
                }
            )
        )
        with self.assertRaises(AccessError):
            printer.with_user(self.printer_user).unlink()

    def test_permissions_create_user(self):
        with self.assertRaises(AccessError):
            self.env["res.remote.printer"].with_user(self.printer_user).create(
                {
                    "remote_id": self.remote.id,
                    "printer_id": self.printer_1.id,
                    "is_default": True,
                }
            )
