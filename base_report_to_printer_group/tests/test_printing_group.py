# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo import exceptions
from odoo.tests.common import TransactionCase

SERVER_MODEL = "odoo.addons.base_report_to_printer.models.printing_server"


class TestPrintingGroup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Models
        cls.XmlAction = cls.env["printing.report.xml.action"]
        cls.Group = cls.env["printing.group"]
        # Existing instances
        cls.format_a4 = cls.env.ref("base.paperformat_euro")
        cls.format_letter = cls.env.ref("base.paperformat_us")
        # Instances
        cls.server = cls.env["printing.server"].create({})
        cls.printer_wh_1 = cls._create_printer("Warehouse 1", cls.format_a4)
        cls.printer_wh_2 = cls._create_printer("Warehouse 2", cls.format_letter)
        cls.printer_office = cls._create_printer("Office", cls.format_a4)
        cls.user = cls.env["res.users"].create(
            {
                "name": "Printing user",
                "login": "printing_user",
                "groups_id": [(6, 0, cls.env.ref("base.group_user").ids)],
            }
        )
        cls.group_wh = cls.Group.create(
            {
                "name": "Warehouse",
                "sequence": 1,
                "user_ids": [(6, 0, cls.user.ids)],
                "printer_ids": [(6, 0, (cls.printer_wh_1 | cls.printer_wh_2).ids)],
            }
        )
        cls.group_office = cls.Group.create(
            {
                "name": "Office",
                "sequence": 2,
                "user_ids": [(6, 0, cls.user.ids)],
            }
        )
        cls.action_server = cls.env["printing.action"].create(
            {"name": "Server", "action_type": "server"}
        )
        cls.report = (
            cls.env["ir.actions.report"]
            .create(
                {
                    "name": "Printing group test",
                    "model": "res.partner",
                    "report_type": "qweb-pdf",
                    "report_name": "base_report_to_printer_group.test",
                    "paperformat_id": cls.format_a4.id,
                    "property_printing_action_id": cls.action_server.id,
                    "printing_printer_id": cls.printer_office.id,
                }
            )
            .with_user(cls.user)
        )
        cls.report = cls.report.sudo()
        # Setup
        cls.cups = mock.patch(f"{SERVER_MODEL}.cups")
        cls.cups.start()
        cls.addClassCleanup(cls.cups.stop)

    @classmethod
    def _create_printer(cls, name, paperformat):
        return cls.env["printing.printer"].create(
            {
                "name": name,
                "system_name": name,
                "server_id": cls.server.id,
                "status": "available",
                "paperformat_ids": [(6, 0, paperformat.ids)],
            }
        )

    def _create_action(self, **values):
        values.setdefault("report_id", self.report.id)
        values.setdefault("action", "server")
        return self.XmlAction.create(values)

    def test_user_or_group_required(self):
        with self.assertRaises(exceptions.ValidationError):
            self._create_action()
        with self.assertRaises(exceptions.ValidationError):
            self._create_action(user_id=self.user.id, group_id=self.group_wh.id)
        self._create_action(group_id=self.group_wh.id)

    def test_user_groups(self):
        self.assertEqual(
            self.user.printing_group_ids, self.group_wh | self.group_office
        )
        self.group_office.active = False
        self.assertEqual(self.user.printing_group_ids, self.group_wh)

    def test_behaviour_group_action(self):
        self.assertEqual(self.report.behaviour()["printer"], self.printer_office)
        self._create_action(
            group_id=self.group_office.id, printer_id=self.printer_wh_2.id
        )
        self.assertEqual(self.report.behaviour()["printer"], self.printer_wh_2)
        self._create_action(group_id=self.group_wh.id, printer_id=self.printer_wh_1.id)
        self.assertEqual(self.report.behaviour()["printer"], self.printer_wh_1)
        self.group_wh.active = False
        self.assertEqual(self.report.behaviour()["printer"], self.printer_wh_2)

    def test_behaviour_user_action_wins(self):
        self._create_action(group_id=self.group_wh.id, printer_id=self.printer_wh_1.id)
        self._create_action(user_id=self.user.id, printer_id=self.printer_office.id)
        self.assertEqual(self.report.behaviour()["printer"], self.printer_office)

    def test_behaviour_other_user_ignores_group(self):
        self._create_action(group_id=self.group_wh.id, printer_id=self.printer_wh_1.id)
        report = self.report.with_user(self.env.ref("base.user_demo")).sudo()
        self.assertEqual(report.behaviour()["printer"], self.printer_office)

    def test_candidate_printers(self):
        self.assertEqual(self.report._get_candidate_printers(), self.printer_wh_1)
        self.group_wh.printer_ids = False
        self.assertEqual(
            self.report._get_candidate_printers(),
            self.printer_wh_1 | self.printer_office,
        )
        self.group_office.printer_ids = self.printer_office
        self.assertEqual(self.report._get_candidate_printers(), self.printer_office)

    def test_other_printers_keep_the_paper_format(self):
        """See more skips the groups, never the paper format"""
        self.assertEqual(self.report._get_candidate_printers(), self.printer_wh_1)
        self.assertEqual(self.report._get_other_printers(), self.printer_office)
        self.report.property_printing_action_id = self.env["printing.action"].create(
            {"name": "Ask", "action_type": "select"}
        )
        result = self.report.print_action_for_report_name(self.report.report_name)
        self.assertEqual(
            [printer["id"] for printer in result["other_printers"]],
            self.printer_office.ids,
        )
