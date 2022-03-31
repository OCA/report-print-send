# Copyright (C) 2018 Florent de Labarre (<https://github.com/fmdl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import mock

from odoo.tests.common import TransactionCase

model = "odoo.addons.base_report_to_printer.models.printing_server"


class TestWizardPrintRecordLabel(TransactionCase):
    def setUp(self):
        super(TestWizardPrintRecordLabel, self).setUp()
        self.Model = self.env["wizard.print.record.label"]
        self.server = self.env["printing.server"].create({})
        self.printer = self.env["printing.printer"].create(
            {
                "name": "Printer",
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
        self.label = self.env["printing.label.zpl2"].create(
            {
                "name": "ZPL II Label",
                "model_id": self.env.ref(
                    "base_report_to_printer.model_printing_printer"
                ).id,
            }
        )

    def test_get_record(self):
        """Check if return a record"""
        self.label.record_id = 10
        res = self.label._get_record()

        Obj = self.env[self.label.model_id.model]
        record = Obj.search([("id", "=", self.label.record_id)], limit=1)
        if not record:
            record = Obj.search([], limit=1, order="id desc")
        self.assertEqual(res, record)

    @mock.patch("%s.cups" % model)
    def test_print_label_test(self, cups):
        """Check if print test"""
        self.label.test_print_mode = True
        self.label.printer_id = self.printer
        self.label.record_id = 10
        self.label.print_test_label()
        cups.Connection().printFile.assert_called_once()

    def test_emulation_without_params(self):
        """Check if not execute next if not in this mode"""
        self.label.test_labelary_mode = False
        self.assertIs(self.label.labelary_image, False)

    def test_emulation_with_bad_header(self):
        """Check if bad header"""
        self.label.test_labelary_mode = True
        self.label.labelary_width = 80
        self.label.labelary_dpmm = "8dpmm"
        self.label.labelary_height = 10000000
        self.env["printing.label.zpl2.component"].create(
            {"name": "ZPL II Label", "label_id": self.label.id, "data": '"Test"'}
        )
        self.assertFalse(self.label.labelary_image)

    def test_emulation_with_bad_data_compute(self):
        """Check if bad data compute"""
        self.label.test_labelary_mode = True
        self.label.labelary_width = 80
        self.label.labelary_height = 30
        self.label.labelary_dpmm = "8dpmm"
        component = self.env["printing.label.zpl2.component"].create(
            {"name": "ZPL II Label", "label_id": self.label.id, "data": "wrong_data"}
        )
        component.unlink()
        self.assertIs(self.label.labelary_image, False)

    def test_emulation_with_good_data(self):
        """Check if ok"""
        self.label.test_labelary_mode = True
        self.label.labelary_width = 80
        self.label.labelary_height = 30
        self.label.labelary_dpmm = "8dpmm"
        self.env["printing.label.zpl2.component"].create(
            {"name": "ZPL II Label", "label_id": self.label.id, "data": '"good_data"'}
        )
        self.assertTrue(self.label.labelary_image)
