# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from .common import PrinterZpl2Common

model = "odoo.addons.base_report_to_printer.models.printing_server"


class TestWizardPrintRecordLabel(PrinterZpl2Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env["wizard.print.record.label"]

    @patch(f"{model}.cups")
    def test_print_record_label(self, cups):
        """Check that printing a label using the generic wizard works"""
        wizard_obj = self.Wizard.with_context(
            active_model="printing.printer",
            active_id=self.printer.id,
            active_ids=[self.printer.id],
            printer_zpl2_id=self.printer.id,
        )
        wizard = wizard_obj.create({})
        self.assertEqual(wizard.printer_id, self.printer)
        self.assertEqual(wizard.label_id, self.label)
        wizard.print_label()
        cups.Connection().printFile.assert_called_once()

    def test_wizard_multiple_printers_and_labels(self):
        """Check that printer_id and label_id are not automatically filled
        when there are multiple possible values
        """
        self.env["printing.printer"].create(
            {
                "name": "Other_Printer",
                "server_id": self.server.id,
                "system_name": "Sys Name",
                "default": True,
                "status": "unknown",
                "status_message": "Msg",
                "model": "res.users",
                "location": "Location",
                "uri": "URI",
            }
        )
        self.env["printing.label.zpl2"].create(
            {
                "name": "Other ZPL II Label",
                "model_id": self.env.ref(
                    "base_report_to_printer.model_printing_printer"
                ).id,
            }
        )
        wizard_obj = self.Wizard.with_context(
            active_model="printing.printer",
            active_id=self.printer.id,
            active_ids=[self.printer.id],
        )
        values = wizard_obj.default_get(["printer_id", "label_id"])
        self.assertEqual(values.get("printer_id", False), False)
        self.assertEqual(values.get("label_id", False), False)

    def test_wizard_multiple_labels_but_on_different_models(self):
        """Check that label_id is automatically filled when there are multiple
        labels, but only one on the right model
        """
        self.env["printing.label.zpl2"].create(
            {
                "name": "Other ZPL II Label",
                "model_id": self.env.ref("base.model_res_users").id,
            }
        )
        wizard_obj = self.Wizard.with_context(
            active_model="printing.printer",
            active_id=self.printer.id,
            active_ids=[self.printer.id],
            printer_zpl2_id=self.printer.id,
        )
        wizard = wizard_obj.create({})
        self.assertEqual(wizard.label_id, self.label)
