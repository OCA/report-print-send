# Copyright (C) 2018 Florent de Labarre (<https://github.com/fmdl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from unittest.mock import patch

import requests

from odoo.tools import mute_logger

from .common import PrinterZpl2Common


class TestWizardPrintRecordLabel(PrinterZpl2Common):
    @classmethod
    def setUpClass(cls):
        cls._super_send = requests.Session.send
        super().setUpClass()

    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        """Don't block external requests."""
        return cls._super_send(s, r, **kw)

    def test_get_record(self):
        """Check if return a record"""
        self.label.record_id = 10
        res = self.label._get_record()

        Obj = self.env[self.label.model_id.model]
        record = Obj.search([("id", "=", self.label.record_id)], limit=1)
        if not record:
            record = Obj.search([], limit=1, order="id desc")
        self.assertEqual(res, record)

    def test_print_label_test(self):
        """Check if print test"""
        self.label.test_print_mode = True
        self.label.printer_id = self.printer
        self.label.record_id = 10
        with patch.object(type(self.printer), "print_document") as mock_print:
            mock_print.return_value = True
            self.label.print_test_label()
            mock_print.assert_called_once()

    def test_emulation_without_params(self):
        """Check if not execute next if not in this mode"""
        self.label.test_labelary_mode = False
        self.assertIs(self.label.labelary_image, False)

    def test_emulation_with_bad_header(self):
        """Check if bad header"""
        self.label.test_labelary_mode = True
        self.label.labelary_width = 80
        self.label.labelary_dpmm = "8dpmm"
        # Maximum label size of 15 x 15 inches
        self.label.labelary_height = 10000000
        self.env["printing.label.zpl2.component"].create(
            {"name": "ZPL II Label", "label_id": self.label.id, "data": '"Test"'}
        )
        # Simulate a 400 response from Labelary (oversized)
        mock_response = requests.Response()
        mock_response.status_code = 400
        # do not log expected warning "Error with Labelary API. 400"
        # "ERROR: Label height is larger than 15.0 inches"
        with (
            patch("requests.post", return_value=mock_response),
            mute_logger("odoo.addons.printer_zpl2.models.printing_label_zpl2"),
        ):
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
        # Mock a successful PNG response from Labelary (minimal 1x1 PNG)
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response._content = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
            b"\x1f\x15\xc4\x89"
            b"\x00\x00\x00\x0aIDAT\x08\x99c\x00\x00\x00\x02\x00\x01\xe5\x27\xde\xfc"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        with patch("requests.post", return_value=mock_response):
            self.assertTrue(self.label.labelary_image)
