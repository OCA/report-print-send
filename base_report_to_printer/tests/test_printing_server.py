# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo import fields
from odoo.tests.common import TransactionCase

model = "odoo.addons.base_report_to_printer.models.printing_server"


class TestPrintingServer(TransactionCase):
    def setUp(self):
        super(TestPrintingServer, self).setUp()
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
    def test_update_printers_error(self, cups):
        """ It should catch any exception from CUPS and update status """
        cups.Connection.side_effect = Exception
        rec_id = self.new_printer()
        self.Model.update_printers()
        self.assertEqual("server-error", rec_id.status)

    @mock.patch("%s.cups" % model)
    def test_update_printers_inits_cups(self, cups):
        """ It should init CUPS connection """
        self.new_printer()
        self.Model.update_printers()
        cups.Connection.assert_called_once_with(
            host=self.server.address, port=self.server.port
        )

    @mock.patch("%s.cups" % model)
    def test_update_printers_gets_all_printers(self, cups):
        """ It should get all printers from CUPS server """
        self.new_printer()
        self.Model.update_printers()
        cups.Connection().getPrinters.assert_called_once_with()

    @mock.patch("%s.cups" % model)
    def test_update_printers_search(self, cups):
        """ It should search all when no domain """
        with mock.patch.object(self.Model, "search") as search:
            self.Model.update_printers()
            search.assert_called_once_with([])

    @mock.patch("%s.cups" % model)
    def test_update_printers_search_domain(self, cups):
        """ It should use specific domain for search """
        with mock.patch.object(self.Model, "search") as search:
            expect = [("id", ">", 0)]
            self.Model.update_printers(expect)
            search.assert_called_once_with(expect)

    @mock.patch("%s.cups" % model)
    def test_update_printers_update_unavailable(self, cups):
        """ It should update status when printer is unavailable """
        rec_id = self.new_printer()
        cups.Connection().getPrinters().get.return_value = False
        self.Model.action_update_printers()
        self.assertEqual("unavailable", rec_id.status)

    @mock.patch("%s.cups" % model)
    def test_update_archived_printers(self, cups):
        """ It should update status even if printer is archived """
        rec_id = self.new_printer()
        rec_id.toggle_active()
        self.server.refresh()
        cups.Connection().getPrinters().get.return_value = False
        self.Model.action_update_printers()
        self.assertEqual(
            "unavailable",
            rec_id.status,
        )

    @mock.patch("%s.cups" % model)
    def test_update_jobs_cron(self, cups):
        """ It should get all jobs from CUPS server """
        self.new_printer()
        self.Model.action_update_jobs()
        cups.Connection().getPrinters.assert_called_once_with()
        cups.Connection().getJobs.assert_called_once_with(
            which_jobs="all",
            first_job_id=-1,
            requested_attributes=[
                "job-name",
                "job-id",
                "printer-uri",
                "job-media-progress",
                "time-at-creation",
                "job-state",
                "job-state-reasons",
                "time-at-processing",
                "time-at-completed",
            ],
        )

    @mock.patch("%s.cups" % model)
    def test_update_jobs_button(self, cups):
        """ It should get all jobs from CUPS server """
        self.new_printer()
        self.server.action_update_jobs()
        cups.Connection().getPrinters.assert_called_once_with()
        cups.Connection().getJobs.assert_called_once_with(
            which_jobs="all",
            first_job_id=-1,
            requested_attributes=[
                "job-name",
                "job-id",
                "printer-uri",
                "job-media-progress",
                "time-at-creation",
                "job-state",
                "job-state-reasons",
                "time-at-processing",
                "time-at-completed",
            ],
        )

    @mock.patch("%s.cups" % model)
    def test_update_jobs_error(self, cups):
        """ It should catch any exception from CUPS and update status """
        cups.Connection.side_effect = Exception
        self.new_printer()
        self.server.update_jobs()
        cups.Connection.assert_called_with(
            host=self.server.address, port=self.server.port
        )

    @mock.patch("%s.cups" % model)
    def test_update_jobs_uncompleted(self, cups):
        """
        It should search which jobs have been completed since last update
        """
        printer = self.new_printer()
        self.new_job(printer, vals={"job_state": "completed"})
        self.new_job(printer, vals={"job_id_cups": 2, "job_state": "processing"})
        self.server.update_jobs(which="not-completed")
        cups.Connection().getJobs.assert_any_call(
            which_jobs="completed",
            first_job_id=2,
            requested_attributes=[
                "job-name",
                "job-id",
                "printer-uri",
                "job-media-progress",
                "time-at-creation",
                "job-state",
                "job-state-reasons",
                "time-at-processing",
                "time-at-completed",
            ],
        )

    @mock.patch("%s.cups" % model)
    def test_update_jobs(self, cups):
        """
        It should update all jobs, known or not
        """
        printer = self.new_printer()
        printer_uri = "hostname:port/" + printer.system_name
        cups.Connection().getJobs.return_value = {
            1: {"printer-uri": printer_uri},
            2: {"printer-uri": printer_uri, "job-state": 9},
            4: {"printer-uri": printer_uri, "job-state": 5},
        }
        self.new_job(printer, vals={"job_state": "completed"})
        completed_job = self.new_job(
            printer, vals={"job_id_cups": 2, "job_state": "processing"}
        )
        purged_job = self.new_job(
            printer, vals={"job_id_cups": 3, "job_state": "processing"}
        )
        self.server.update_jobs()
        new_job = self.env["printing.job"].search([("job_id_cups", "=", 4)])
        self.assertEqual(completed_job.job_state, "completed")
        self.assertEqual(purged_job.active, False)
        self.assertEqual(new_job.job_state, "processing")
