# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import errno
import tempfile
from unittest import mock

from odoo.addons.base_report_to_printer.tests.test_printing_printer_tray import (
    TestPrintingPrinter,
)

model = "odoo.addons.base_report_to_printer_cups.models.printing_printer"
server_model = "odoo.addons.base_report_to_printer_cups.models.printing_server"

ppd_header = '*PPD-Adobe: "4.3"'
ppd_input_slot_header = """
*OpenUI *InputSlot: PickOne
*DefaultInputSlot: Auto
*InputSlot Auto/Auto (Default): "
    << /DeferredMediaSelection true /ManualFeed false
        /MediaPosition null /MediaType null >> setpagedevice
        userdict /TSBMediaType 0 put"
*End
"""
ppd_input_slot_body = """
*InputSlot {name}/{text}: "
    << /DeferredMediaSelection true /ManualFeed false
        /MediaPosition null /MediaType null >> setpagedevice
        userdict /TSBMediaType 0 put"
*End
"""
ppd_input_slot_footer = """
*CloseUI: *InputSlot
"""
ppd_output_slot_header = """
*OpenUI *OutputBin/Output Tray: PickOne
*OrderDependency: 40 AnySetup *OutputBin
*DefaultOutputBin: Default
*OutputBin Default/Default: "
    << /OutputType (Default) >> setpagedevice"
"""
ppd_output_slot_body = """
*OutputBin {name}/{text}: "
    << /OutputType (Bin{nb}) >> setpagedevice"
"""
ppd_output_slot_footer = """
*CloseUI: *OutputBin
"""


class TestPrintingPrinterCups(TestPrintingPrinter):
    def setUp(self):
        super().setUp()
        self.server = self.env["printing.server"].create({})
        self.printer = self.env["printing.printer"].create(
            {
                "name": "",
                "system_name": "Sys Name",
                "server_id": self.server.id,
                "backend": "cups",
                "default": True,
                "status": "unknown",
                "status_message": "Msg",
                "model": "res.users",
                "location": "Location",
                "uri": "URI",
            }
        )

    def build_ppd(self, input_slots=None):
        ppd_contents = ppd_header
        ppd_contents += ppd_input_slot_header
        if input_slots:
            for input_slot in input_slots:
                ppd_contents += ppd_input_slot_body.format(
                    name=input_slot["name"], text=input_slot["text"]
                )
        ppd_contents += ppd_input_slot_footer
        return ppd_contents

    def mock_cups_ppd(self, cups, file_name=None, input_slots=None):
        if file_name is None:
            fd, file_name = tempfile.mkstemp()

        ppd_contents = self.build_ppd(input_slots)
        with open(file_name, "w") as fp:
            fp.write(ppd_contents)

        cups.Connection().getPPD3.return_value = (200, 0, file_name)
        cups.Connection().getPrinters.return_value = {
            self.printer.system_name: {
                "printer-info": "info",
                "printer-uri-supported": "uri",
            }
        }

    @mock.patch(f"{server_model}.cups")
    def test_update_printers(self, cups):
        """
        Check that the update_printers method calls _prepare_update_from_cups
        """
        self.mock_cups_ppd(cups, file_name=False)
        self.env["printing.server"].update_printers()
        self.assertEqual(self.printer.name, "info")
        self.printer.name = "My custom name"
        self.env["printing.server"].update_printers()
        self.assertEqual(self.printer.name, "My custom name")

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups_no_ppd(self, cups):
        self.mock_cups_ppd(cups, file_name=False)
        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]
        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertNotIn("input_tray_ids", vals)

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups_empty_ppd(self, cups):
        fd, file_name = tempfile.mkstemp()
        self.mock_cups_ppd(cups, file_name=file_name)
        with open(file_name, "w") as fp:
            fp.write(ppd_header)
        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]
        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertNotIn("input_tray_ids", vals)

    @mock.patch(f"{server_model}.cups")
    @mock.patch("os.unlink")
    def test_prepare_update_from_cups_unlink_error(self, os_unlink, cups):
        os_unlink.side_effect = OSError(errno.EIO, "Error")
        self.mock_cups_ppd(cups)
        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]
        with self.assertRaises(OSError):
            self.printer._prepare_update_from_cups(connection, cups_printer)

    @mock.patch(f"{server_model}.cups")
    @mock.patch("os.unlink")
    def test_prepare_update_from_cups_unlink_error_enoent(self, os_unlink, cups):
        os_unlink.side_effect = OSError(errno.ENOENT, "Error")
        self.mock_cups_ppd(cups)
        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]
        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(
            vals["input_tray_ids"],
            [(0, 0, {"name": "Auto (Default)", "system_name": "Auto"})],
        )

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups(self, cups):
        self.mock_cups_ppd(cups)
        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]
        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(
            vals["input_tray_ids"],
            [(0, 0, {"name": "Auto (Default)", "system_name": "Auto"})],
        )

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups_with_multiple_trays(self, cups):
        self.mock_cups_ppd(cups, input_slots=[{"name": "Tray1", "text": "Tray 1"}])
        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]
        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertCountEqual(
            vals["input_tray_ids"],
            [
                (0, 0, {"name": "Auto (Default)", "system_name": "Auto"}),
                (0, 0, {"name": "Tray 1", "system_name": "Tray1"}),
            ],
        )

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups_already_known_trays(self, cups):
        self.mock_cups_ppd(cups, input_slots=[{"name": "Tray1", "text": "Tray 1"}])
        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]
        self.env["printing.tray.input"].create(
            {"name": "Tray1", "system_name": "Tray1", "printer_id": self.printer.id}
        )
        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(
            vals["input_tray_ids"],
            [(0, 0, {"name": "Auto (Default)", "system_name": "Auto"})],
        )

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups_unknown_trays(self, cups):
        self.mock_cups_ppd(cups)
        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]
        tray = self.env["printing.tray.input"].create(
            {"name": "Tray", "system_name": "TrayName", "printer_id": self.printer.id}
        )
        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(
            vals["input_tray_ids"],
            [(0, 0, {"name": "Auto (Default)", "system_name": "Auto"}), (2, tray.id)],
        )
