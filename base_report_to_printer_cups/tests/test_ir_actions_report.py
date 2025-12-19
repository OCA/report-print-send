# Copyright 2016 LasLabs Inc.
# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from unittest import mock

from odoo.addons.base_report_to_printer.tests.test_ir_actions_report import (
    TestIrActionsReportXml,
)

model = "odoo.addons.base.models.ir_actions_report.IrActionsReport"


class TestIrActionsReportCups(TestIrActionsReportXml):
    def setUp(self):
        super().setUp()
        self.cups_server = self.env["printing.server"].create({"name": "CUPS Server"})
        if hasattr(self, "printer"):
            self.printer.write(
                {
                    "backend": "cups",
                    "status": "error",
                    "server_id": self.cups_server.id,
                }
            )
            self.report.write({"printing_printer_id": self.printer.id})

    def new_printer(self):
        return self.env["printing.printer"].create(
            {
                "name": "CUPS Printer",
                "system_name": "cups_printer",
                "backend": "cups",
                "status": "error",
                "server_id": self.cups_server.id,
            }
        )

    def test_print_in_new_thread(self):
        """It should return the action and printer from printing action in other
        thread"""
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "server"
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env.user
        printing_action.printer_id = self.new_printer()
        printing_action.printer_id.multi_thread = True
        with (
            mock.patch(
                "odoo.addons.base_report_to_printer.models.printing_printer.PrintingPrinter.print_document",
                side_effect=Exception("simulated print failure"),
            ),
            self.assertLogs(
                "odoo.addons.base_report_to_printer_cups", level="WARNING"
            ) as logs,
        ):
            report.print_document_client_action([1])
            self.assertGreaterEqual(len(logs.records), 1)
            for record in logs.records:
                self.assertEqual(record.levelno, logging.WARNING)

    def test_behaviour_user_values(self):
        with self.assertLogs(
            "odoo.addons.base_report_to_printer_cups", level="WARNING"
        ) as logs:
            result = super().test_behaviour_user_values()
            self.assertGreaterEqual(len(logs.records), 1)
            for record in logs.records:
                self.assertEqual(record.levelno, logging.WARNING)
            return result

    def test_behaviour_report_values(self):
        with self.assertLogs(
            "odoo.addons.base_report_to_printer_cups", level="WARNING"
        ) as logs:
            result = super().test_behaviour_report_values()
            self.assertGreaterEqual(len(logs.records), 1)
            for record in logs.records:
                self.assertEqual(record.levelno, logging.WARNING)
            return result

    def test_behaviour_printing_action_with_printer(self):
        with self.assertLogs(
            "odoo.addons.base_report_to_printer_cups", level="WARNING"
        ) as logs:
            result = super().test_behaviour_printing_action_with_printer()
            self.assertGreaterEqual(len(logs.records), 1)
            for record in logs.records:
                self.assertEqual(record.levelno, logging.WARNING)
            return result
