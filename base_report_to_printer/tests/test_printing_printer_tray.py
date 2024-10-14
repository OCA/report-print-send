# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import errno
import tempfile
from unittest import mock

from odoo.tests.common import TransactionCase

model = "odoo.addons.base_report_to_printer.models.printing_printer"
server_model = "odoo.addons.base_report_to_printer.models.printing_server"

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


class TestPrintingPrinter(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Model = self.env["printing.printer"]
        self.ServerModel = self.env["printing.server"]
        self.server = self.env["printing.server"].create({})
        self.printer = self.env["printing.printer"].create(
            {
                "name": "",
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
        self.tray_vals = {
            "name": "Tray",
            "system_name": "TrayName",
            "printer_id": self.printer.id,
        }

    def new_tray(self, vals=None):
        values = self.tray_vals
        if vals is not None:
            values.update(vals)
        return self.env["printing.tray"].create(values)

    def build_ppd(self, input_slots=None):
        """
        Builds a fake PPD file declaring defined input slots
        """
        ppd_contents = ppd_header
        ppd_contents += ppd_input_slot_header
        if input_slots is not None:
            for input_slot in input_slots:
                ppd_contents += ppd_input_slot_body.format(
                    name=input_slot["name"], text=input_slot["text"]
                )
        ppd_contents += ppd_input_slot_footer

        return ppd_contents

    def mock_cups_ppd(self, cups, file_name=None, input_slots=None):
        """
        Create a fake PPD file (if needed), then mock the getPPD3 method
        return value to give that file
        """
        if file_name is None:
            fd, file_name = tempfile.mkstemp()

        if file_name:
            ppd_contents = self.build_ppd(input_slots=input_slots)
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
        self.ServerModel.update_printers()
        self.assertEqual(self.printer.name, "info")
        self.printer.name = "My custom name"
        self.ServerModel.update_printers()
        self.assertEqual(self.printer.name, "My custom name")

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups_no_ppd(self, cups):
        """
        Check that the tray_ids field has no value when no PPD is available
        """
        self.mock_cups_ppd(cups, file_name=False)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertFalse("tray_ids" in vals)

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups_empty_ppd(self, cups):
        """
        Check that the tray_ids field has no value when the PPD file has
        no input slot declared
        """
        fd, file_name = tempfile.mkstemp()
        self.mock_cups_ppd(cups, file_name=file_name)
        # Replace the ppd file's contents by an empty file
        with open(file_name, "w") as fp:
            fp.write(ppd_header)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertFalse("tray_ids" in vals)

    @mock.patch(f"{server_model}.cups")
    @mock.patch("os.unlink")
    def test_prepare_update_from_cups_unlink_error(self, os_unlink, cups):
        """
        When OSError other than ENOENT is encountered, the exception is raised
        """
        # Break os.unlink
        os_unlink.side_effect = OSError(errno.EIO, "Error")

        self.mock_cups_ppd(cups)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        with self.assertRaises(OSError):
            self.printer._prepare_update_from_cups(connection, cups_printer)

    @mock.patch(f"{server_model}.cups")
    @mock.patch("os.unlink")
    def test_prepare_update_from_cups_unlink_error_enoent(self, os_unlink, cups):
        """
        When a ENOENT error is encountered, the file has already been unlinked
        This is not an issue, as we were trying to delete the file.
        The update can continue.
        """
        # Break os.unlink
        os_unlink.side_effect = OSError(errno.ENOENT, "Error")

        self.mock_cups_ppd(cups)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(
            vals["tray_ids"],
            [(0, 0, {"name": "Auto (Default)", "system_name": "Auto"})],
        )

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups(self, cups):
        """
        Check the return value when adding a single tray
        """
        self.mock_cups_ppd(cups)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(
            vals["tray_ids"],
            [(0, 0, {"name": "Auto (Default)", "system_name": "Auto"})],
        )

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups_with_multiple_trays(self, cups):
        """
        Check the return value when adding multiple trays at once
        """
        self.mock_cups_ppd(cups, input_slots=[{"name": "Tray1", "text": "Tray 1"}])

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertItemsEqual(
            vals["tray_ids"],
            [
                (0, 0, {"name": "Auto (Default)", "system_name": "Auto"}),
                (0, 0, {"name": "Tray 1", "system_name": "Tray1"}),
            ],
        )

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups_already_known_trays(self, cups):
        """
        Check that calling the method twice doesn't create the trays multiple
        times
        """
        self.mock_cups_ppd(cups, input_slots=[{"name": "Tray1", "text": "Tray 1"}])

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        # Create a tray which is in the PPD file
        self.new_tray({"system_name": "Tray1"})

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(
            vals["tray_ids"],
            [(0, 0, {"name": "Auto (Default)", "system_name": "Auto"})],
        )

    @mock.patch(f"{server_model}.cups")
    def test_prepare_update_from_cups_unknown_trays(self, cups):
        """
        Check that trays which are not in the PPD file are removed from Odoo
        """
        self.mock_cups_ppd(cups)

        connection = cups.Connection()
        cups_printer = connection.getPrinters()[self.printer.system_name]

        # Create a tray which is absent from the PPD file
        tray = self.new_tray()

        vals = self.printer._prepare_update_from_cups(connection, cups_printer)
        self.assertEqual(
            vals["tray_ids"],
            [(0, 0, {"name": "Auto (Default)", "system_name": "Auto"}), (2, tray.id)],
        )
