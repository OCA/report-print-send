from unittest import mock

from odoo import fields
from odoo.tests.common import TransactionCase


class TestPrintingJob(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Job = self.env["printing.job"]
        self.Printer = self.env["printing.printer"]
        self.printer_vals = {
            "name": "Printer",
            "system_name": "Sys Name",
            "default": True,
            "status": "unknown",
            "status_message": "Msg",
            "model": "res.users",
            "location": "Location",
            "uri": "URI",
        }
        self.job_vals = {
            "time_at_creation": fields.Datetime.now(),
        }

    def new_printer(self):
        return self.Printer.create(self.printer_vals)

    def new_job(self, printer, extra_vals=None):
        vals = {**self.job_vals, **(extra_vals or {})}
        vals["printer_id"] = printer.id
        return self.Job.create(vals)

    def test_action_cancel_delegates_to_cancel(self):
        """action_cancel should call cancel() and return its result."""

        printer = self.new_printer()
        job = self.new_job(printer)

        with mock.patch(
            "odoo.addons.base_report_to_printer.models.printing_job.PrintingJob.cancel",
            autospec=True,
            return_value="ok",
        ) as cancel:
            result = job.action_cancel()

        cancel.assert_called_once_with(job)
        self.assertEqual(result, "ok")

    def test_action_cancel_requires_singleton(self):
        """action_cancel should enforce a single recordset."""

        printer = self.new_printer()
        job1 = self.new_job(printer)
        job2 = self.new_job(printer)

        with self.assertRaises(ValueError):
            (job1 | job2).action_cancel()

    def test_cancel_returns_true(self):
        """Base cancel should return True to allow chaining in overrides."""

        printer = self.new_printer()
        job = self.new_job(printer)

        self.assertTrue(job.cancel())
