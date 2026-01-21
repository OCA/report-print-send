# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo.addons.base_report_to_printer.tests.test_printing_printer import (
    TestPrintingPrinterBase,
)


class TestPrintingPrinterBaseCups(TestPrintingPrinterBase):
    def setUp(self):
        super().setUp()

        self.server = self.env["printing.server"].create({})
        self.printer_vals.update({"server_id": self.server.id, "backend": "cups"})

    @mock.patch("cups.Connection")
    @mock.patch("os.remove", side_effect=FileNotFoundError)
    def test_print_file(self, mock_remove, cups_conn_mock):
        import logging

        self.printer = self.new_record()
        cups_conn_mock.return_value.printFile.return_value = True
        file_name = "/tmp/file.pdf"
        with self.assertLogs(level=logging.WARNING) as logs:
            self.assertTrue(self.printer.print_file(file_name, "report"))
        cups_conn_mock.return_value.printFile.assert_called_once()
        mock_remove.assert_called_once_with(file_name)
        self.assertEqual(len(logs.records), 1)
        self.assertEqual(logs.records[0].levelno, logging.WARNING)

    @mock.patch("cups.Connection")
    def test_cancel_all_jobs(self, cups_conn_mock):
        self.printer = self.new_record()
        cups_conn_mock.return_value.cancelAllJobs.return_value = True
        self.assertTrue(self.printer.cancel_all_jobs())

    @mock.patch("cups.Connection")
    def test_enable_disable_printer(self, cups_conn_mock):
        self.printer = self.new_record()
        cups_conn_mock.return_value.enablePrinter.return_value = True
        cups_conn_mock.return_value.disablePrinter.return_value = True
        self.assertTrue(self.printer.enable())
        self.assertTrue(self.printer.disable())

    @mock.patch("cups.Connection")
    def test_print_test_page(self, cups_conn_mock):
        self.printer = self.new_record()
        cups_conn_mock.return_value.printTestPage.return_value = True
        self.assertTrue(self.printer.print_test_page())
