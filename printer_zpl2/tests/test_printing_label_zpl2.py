# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo import exceptions
from odoo.tests.common import TransactionCase

from ..models import zpl2

model = "odoo.addons.base_report_to_printer.models.printing_server"


class TestPrintingLabelZpl2(TransactionCase):
    def setUp(self):
        super(TestPrintingLabelZpl2, self).setUp()
        self.Model = self.env["printing.label.zpl2"]
        self.ComponentModel = self.env["printing.label.zpl2.component"]
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
        self.label_vals = {
            "name": "ZPL II Label",
            "model_id": self.env.ref(
                "base_report_to_printer.model_printing_printer"
            ).id,
        }
        self.component_vals = {"name": "ZPL II Label Component"}

    def new_label(self, vals=None):
        values = self.label_vals.copy()
        if vals:
            values.update(vals)
        return self.Model.create(values)

    def new_component(self, vals=None):
        values = self.component_vals.copy()
        if vals:
            values.update(vals)
        return self.ComponentModel.create(values)

    def test_print_on_bad_model(self):
        """Check that printing on the bad model raises an exception"""
        label = self.new_label()
        with self.assertRaises(exceptions.UserError):
            label.print_label(self.printer, label)

    @mock.patch("%s.cups" % model)
    def test_print_empty_label(self, cups):
        """Check that printing an empty label works"""
        label = self.new_label()
        label.print_label(self.printer, self.printer)
        cups.Connection().printFile.assert_called_once()

    def test_empty_label_contents(self):
        """Check contents of an empty label"""
        label = self.new_label()
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ",
        )

    def test_sublabel_label_contents(self):
        """Check contents of a sublabel label component"""
        sublabel = self.new_label({"name": "Sublabel"})
        data = "Some text"
        self.new_component({"label_id": sublabel.id, "data": '"' + data + '"'})
        label = self.new_label()
        self.new_component(
            {
                "label_id": label.id,
                "name": "Sublabel contents",
                "component_type": "sublabel",
                "sublabel_id": sublabel.id,
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Sublabel component position
            # Position 30x30 because the default values are :
            # - 10x10 for the sublabel component in the main label
            # - 10x10 for the sublabel in the sublabel component
            # - 10x10 for the component in the sublabel
            "^FO30,30"
            # Sublabel component format
            "^A0N,10,10"
            # Sublabel component contents
            "^FD{contents}"
            # Sublabel component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_repeatable_component_label_fixed_contents(self):
        """Check contents of a repeatable label component

        Check that a fixed value is repeated each time
        """
        label = self.new_label(
            {"model_id": self.env.ref("printer_zpl2.model_printing_label_zpl2").id}
        )
        data = "Some text"
        self.new_component(
            {
                "label_id": label.id,
                "data": '"' + data + '"',
                "repeat": True,
                "repeat_count": 3,
                "repeat_offset_y": 15,
            }
        )
        contents = label._generate_zpl2_data(label).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # First component position
            "^FO10,10"
            # First component format
            "^A0N,10,10"
            # First component contents
            "^FD{contents}"
            # First component end
            "^FS\n"
            # Second component position
            "^FO10,25"
            # Second component format
            "^A0N,10,10"
            # Second component contents
            "^FD{contents}"
            # Second component end
            "^FS\n"
            # Third component position
            "^FO10,40"
            # Third component format
            "^A0N,10,10"
            # Third component contents
            "^FD{contents}"
            # Third component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_repeatable_component_label_iterable_contents(self):
        """Check contents of a repeatable label component

        Check that an iterable contents (list, tuple, etc.) is browsed
        If the repeat_count is higher than the value length, all values are
        displayed
        """
        label = self.new_label(
            {"model_id": self.env.ref("printer_zpl2.model_printing_label_zpl2").id}
        )
        data = ["First text", "Second text", "Third text"]
        self.new_component(
            {
                "label_id": label.id,
                "data": str(data),
                "repeat": True,
                "repeat_offset": 1,
                "repeat_count": 3,
                "repeat_offset_y": 15,
            }
        )
        contents = label._generate_zpl2_data(label).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # First component position
            "^FO10,10"
            # First component format
            "^A0N,10,10"
            # First component contents
            "^FD{contents[1]}"
            # First component end
            "^FS\n"
            # Second component position
            "^FO10,25"
            # Second component format
            "^A0N,10,10"
            # Second component contents
            "^FD{contents[2]}"
            # Second component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_repeatable_component_label_iterable_offset(self):
        """Check contents of a repeatable label component with an offset

        Check that an iterable contents (list, tuple, etc.) is browsed
        If the repeat_count is higher than the value length, all values are
        displayed
        """
        label = self.new_label(
            {"model_id": self.env.ref("printer_zpl2.model_printing_label_zpl2").id}
        )
        data = ["Text {value}".format(value=ind) for ind in range(20)]
        self.new_component(
            {
                "label_id": label.id,
                "data": str(data),
                "repeat": True,
                "repeat_offset": 10,
                "repeat_count": 3,
                "repeat_offset_y": 15,
            }
        )
        contents = label._generate_zpl2_data(label).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # First component position
            "^FO10,10"
            # First component format
            "^A0N,10,10"
            # First component contents
            "^FD{contents[10]}"
            # First component end
            "^FS\n"
            # Second component position
            "^FO10,25"
            # Second component format
            "^A0N,10,10"
            # Second component contents
            "^FD{contents[11]}"
            # Second component end
            "^FS\n"
            # Third component position
            "^FO10,40"
            # Third component format
            "^A0N,10,10"
            # Third component contents
            "^FD{contents[12]}"
            # Third component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_repeatable_sublabel_contents(self):
        """Check contents of a repeatable sublabel label component"""
        sublabel = self.new_label(
            {
                "name": "Sublabel",
                "model_id": self.env.ref(
                    "printer_zpl2.model_printing_label_zpl2_component"
                ).id,
            }
        )
        self.new_component(
            {"label_id": sublabel.id, "name": "Components name", "data": "object.name"}
        )
        self.new_component(
            {
                "label_id": sublabel.id,
                "name": "Components data",
                "data": "object.data",
                "origin_x": 50,
            }
        )
        label = self.new_label(
            {"model_id": self.env.ref("printer_zpl2.model_printing_label_zpl2").id}
        )
        self.new_component(
            {"label_id": label.id, "name": "Label name", "data": "object.name"}
        )
        self.new_component(
            {
                "label_id": label.id,
                "name": "Label components",
                "component_type": "sublabel",
                "origin_x": 15,
                "origin_y": 30,
                "data": "object.component_ids",
                "sublabel_id": sublabel.id,
                "repeat": True,
                "repeat_count": 3,
                "repeat_offset_y": 15,
            }
        )
        contents = label._generate_zpl2_data(label).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Label name component position
            "^FO10,10"
            # Label name component format
            "^A0N,10,10"
            # Label name component contents
            "^FD{label.name}"
            # Label name component end
            "^FS\n"
            # First component name component position
            "^FO35,50"
            # First component name component format
            "^A0N,10,10"
            # First component name component contents
            "^FD{label.component_ids[0].name}"
            # First component name component end
            "^FS\n"
            # First component data component position
            "^FO75,50"
            # First component data component format
            "^A0N,10,10"
            # First component data component contents
            "^FD{label.component_ids[0].data}"
            # First component data component end
            "^FS\n"
            # Second component name component position
            "^FO35,65"
            # Second component name component format
            "^A0N,10,10"
            # Second component name component contents
            "^FD{label.component_ids[1].name}"
            # Second component name component end
            "^FS\n"
            # Second component data component position
            "^FO75,65"
            # Second component data component format
            "^A0N,10,10"
            # Second component data component contents
            "^FD{label.component_ids[1].data}"
            # Second component data component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(label=label),
        )

    def test_text_label_contents(self):
        """Check contents of a text label"""
        label = self.new_label()
        data = "Some text"
        self.new_component({"label_id": label.id, "data": '"%s"' % data})
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Component position
            "^FO10,10"
            # Component format
            "^A0N,10,10"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_reversed_text_label_contents(self):
        """Check contents of a text label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {"label_id": label.id, "data": '"' + data + '"', "reverse_print": True}
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Component position
            "^FO10,10"
            # Component format
            "^A0N,10,10"
            # Reverse print argument
            "^FR"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_block_text_label_contents(self):
        """Check contents of a text label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {"label_id": label.id, "data": '"' + data + '"', "in_block": True}
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Component position
            "^FO10,10"
            # Component format
            "^A0N,10,10"
            # Block definition
            "^FB0,1,0,L,0"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_rectangle_label_contents(self):
        """Check contents of a rectangle label"""
        label = self.new_label()
        self.new_component({"label_id": label.id, "component_type": "rectangle"})
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Component position
            "^FO10,10"
            # Component format
            "^GB1,1,1,B,0"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ",
        )

    def test_diagonal_line_label_contents(self):
        """Check contents of a diagonal line label"""
        label = self.new_label()
        self.new_component({"label_id": label.id, "component_type": "diagonal"})
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Component position
            "^FO10,10"
            # Component format
            "^GD3,3,1,B,L"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ",
        )

    def test_circle_label_contents(self):
        """Check contents of a circle label"""
        label = self.new_label()
        self.new_component({"label_id": label.id, "component_type": "circle"})
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Component position
            "^FO10,10"
            # Component format
            "^GC3,2,B"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ",
        )

    def test_code11_barcode_label_contents(self):
        """Check contents of a code 11 barcode label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "code_11",
                "data": '"' + data + '"',
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^B1N,N,0,N,N"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_2of5_barcode_label_contents(self):
        """Check contents of a interleaved 2 of 5 barcode label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "interleaved_2_of_5",
                "data": '"' + data + '"',
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^B2N,0,N,N,N"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_code39_barcode_label_contents(self):
        """Check contents of a code 39 barcode label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "code_39",
                "data": '"' + data + '"',
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^B3N,N,0,N,N"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_code49_barcode_label_contents(self):
        """Check contents of a code 49 barcode label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "code_49",
                "data": '"' + data + '"',
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^B4N,0,N"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_code49_barcode_label_contents_line(self):
        """Check contents of a code 49 barcode label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "code_49",
                "data": '"' + data + '"',
                "interpretation_line": True,
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^B4N,0,B"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_code49_barcode_label_contents_with_above(self):
        """Check contents of a code 49 barconde label
        with interpretation line above
        """
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "code_49",
                "data": '"' + data + '"',
                "interpretation_line": True,
                "interpretation_line_above": True,
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^B4N,0,A"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_pdf417_barcode_label_contents(self):
        """Check contents of a pdf417 barcode label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {"label_id": label.id, "component_type": "pdf417", "data": '"' + data + '"'}
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^B7N,0,0,0,0,N"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_ean8_barcode_label_contents(self):
        """Check contents of a ean-8 barcode label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {"label_id": label.id, "component_type": "ean-8", "data": '"' + data + '"'}
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^B8N,0,N,N"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_upce_barcode_label_contents(self):
        """Check contents of a upc-e barcode label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {"label_id": label.id, "component_type": "upc-e", "data": '"' + data + '"'}
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^B9N,0,N,N,N"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_code128_barcode_label_contents(self):
        """Check contents of a code 128 barcode label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "code_128",
                "data": '"' + data + '"',
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^BCN,0,N,N,N"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_ean13_barcode_label_contents(self):
        """Check contents of a ean-13 barcode label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {"label_id": label.id, "component_type": "ean-13", "data": '"' + data + '"'}
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^BEN,0,N,N"
            # Component contents
            "^FD{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_qrcode_barcode_label_contents(self):
        """Check contents of a qr code barcode label"""
        label = self.new_label()
        data = "Some text"
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "qr_code",
                "data": '"' + data + '"',
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            # Label start
            "^XA\n"
            # Print width
            "^PW480\n"
            # UTF-8 encoding
            "^CI28\n"
            # Label position
            "^LH10,10\n"
            # Barcode default format
            "^BY2,3.0"
            # Component position
            "^FO10,10"
            # Component format
            "^BQN,2,1,Q,7"
            # Component contents
            "^FDQA,{contents}"
            # Component end
            "^FS\n"
            # Recall last saved parameters
            "^JUR\n"
            # Label end
            "^XZ".format(contents=data),
        )

    def test_graphic_label_contents_blank(self):
        """Check contents of a image label"""
        label = self.new_label()
        data = "R0lGODlhAQABAIAAAP7//wAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw=="
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "graphic",
                "data": '"' + data + '"',
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            "^XA\n"
            "^PW480\n"
            "^CI28\n"
            "^LH10,10\n"
            "^FO10,10^GFA,1.0,1.0,1.0,b'00'^FS\n"
            "^JUR\n"
            "^XZ",
        )

    def test_graphic_label_contents_blank_rotated(self):
        """Check contents of image rotated label"""
        label = self.new_label()
        data = "R0lGODlhAQABAIAAAP7//wAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw=="
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "graphic",
                "data": '"' + data + '"',
                "height": 10,
                "width": 10,
                "reverse_print": 1,
                "orientation": zpl2.ORIENTATION_ROTATED,
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            "^XA\n"
            "^PW480\n"
            "^CI28\n"
            "^LH10,10\n"
            "^FO10,10^GFA,20.0,20.0,2.0,"
            "b'FFC0FFC0FFC0FFC0FFC0FFC0FFC0FFC0FFC0FFC0'^FS\n"
            "^JUR\n"
            "^XZ",
        )

    def test_graphic_label_contents_blank_inverted(self):
        """Check contents of a image inverted label"""
        label = self.new_label()
        data = "R0lGODlhAQABAIAAAP7//wAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw=="
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "graphic",
                "data": '"' + data + '"',
                "orientation": zpl2.ORIENTATION_INVERTED,
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            "^XA\n"
            "^PW480\n"
            "^CI28\n"
            "^LH10,10\n"
            "^FO10,10^GFA,1.0,1.0,1.0,b'00'^FS\n"
            "^JUR\n"
            "^XZ",
        )

    def test_graphic_label_contents_blank_bottom(self):
        """Check contents of a image bottom label"""
        label = self.new_label()
        data = "R0lGODlhAQABAIAAAP7//wAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw=="
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "graphic",
                "data": '"' + data + '"',
                "orientation": zpl2.ORIENTATION_BOTTOM_UP,
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            "^XA\n"
            "^PW480\n"
            "^CI28\n"
            "^LH10,10\n"
            "^FO10,10^GFA,1.0,1.0,1.0,b'00'^FS\n"
            "^JUR\n"
            "^XZ",
        )

    def test_zpl2_raw_contents_blank(self):
        """Check contents of a image label"""
        label = self.new_label()
        data = "^FO50,50^GB100,100,100^FS"
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "zpl2_raw",
                "data": '"' + data + '"',
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents,
            "^XA\n"
            "^PW480\n"
            "^CI28\n"
            "^LH10,10\n"
            "^FO50,50^GB100,100,100^FS\n"
            "^JUR\n"
            "^XZ",
        )

    def test_zpl2_component_not_show(self):
        """Check to don't show no things"""
        label = self.new_label()
        data = "component_not_show"
        self.new_component(
            {
                "label_id": label.id,
                "component_type": "zpl2_raw",
                "data": '"' + data + '"',
            }
        )
        contents = label._generate_zpl2_data(self.printer).decode("utf-8")
        self.assertEqual(
            contents, "^XA\n" "^PW480\n" "^CI28\n" "^LH10,10\n" "^JUR\n" "^XZ"
        )

    def test_zpl2_component_quick_move(self):
        """Check component quick move"""
        label = self.new_label()
        component = self.new_component(
            {
                "label_id": label.id,
                "component_type": "zpl2_raw",
                "data": '""',
                "origin_x": 20,
                "origin_y": 30,
            }
        )
        component.action_plus_origin_x()
        self.assertEqual(30, component.origin_x)
        component.action_minus_origin_x()
        self.assertEqual(20, component.origin_x)
        component.action_plus_origin_y()
        self.assertEqual(40, component.origin_y)
        component.action_minus_origin_y()
        self.assertEqual(30, component.origin_y)
