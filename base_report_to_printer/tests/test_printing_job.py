# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo import fields
from odoo.tests.common import TransactionCase

model = "odoo.addons.base_report_to_printer.models.printing_server"


class TestPrintingJob(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Model = self.env["printing.server"]
        self.server = self.Model.create({})
        self.printer_vals = {
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
        self.job_vals = {
            "server_id": self.server.id,
            "job_id_cups": 1,
            "job_media_progress": 0,
            "time_at_creation": fields.Datetime.now(),
        }

    def new_printer(self):
        return self.env["printing.printer"].create(self.printer_vals)

    def new_job(self, printer, vals=None):
        values = self.job_vals
        if vals is not None:
            values.update(vals)
        values["printer_id"] = printer.id
        return self.env["printing.job"].create(values)

    @mock.patch("%s.cups" % model)
    def test_cancel_job_error(self, cups):
        """It should catch any exception from CUPS and update status"""
        cups.Connection.side_effect = Exception
        printer = self.new_printer()
        job = self.new_job(printer, {"job_id_cups": 2})
        job.action_cancel()
        cups.Connection.side_effect = None
        self.assertEqual(cups.Connection().cancelJob.call_count, 0)

    @mock.patch("%s.cups" % model)
    def test_cancel_job(self, cups):
        """It should catch any exception from CUPS and update status"""
        printer = self.new_printer()
        job = self.new_job(printer)
        job.cancel()
        cups.Connection().cancelJob.assert_called_once_with(
            job.job_id_cups, purge_job=False
        )
