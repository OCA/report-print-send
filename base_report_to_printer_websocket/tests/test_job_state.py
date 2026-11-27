# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from unittest import mock

from odoo.tests import HttpCase, new_test_user, tagged

from ..models.printing_job import PrintingJob


@tagged("post_install", "-at_install")
class TestJobState(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent = new_test_user(
            cls.env, login="agent", password="agent", groups="base.group_portal"
        )
        cls.other_agent = new_test_user(
            cls.env, login="other", password="other", groups="base.group_portal"
        )
        cls.printer = cls.env["printing.printer"].create(
            {
                "name": "Staging",
                "system_name": "Staging",
                "backend": "websocket",
                "websocket_user_id": cls.agent.id,
            }
        )
        cls.report = cls.env["ir.actions.report"].search([], limit=1)

    def _send(self):
        with mock.patch.object(type(self.env["bus.bus"]), "_sendone") as sendone:
            job = self.printer.print_document(
                self.report, b"%PDF-1.4 test", title="SO001"
            )
        self.assertEqual(sendone.call_args.args[2]["job_uuid"], job.websocket_uuid)
        return job

    def _report(self, login, **params):
        self.authenticate(login, login)
        return self.url_open(
            "/printing/websocket/job/state",
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}),
            headers={"Content-Type": "application/json"},
        ).json()

    def test_agent_reports_the_job_out_of_the_queue(self):
        job = self._send()
        self.assertEqual(job.name, "SO001")
        self.assertEqual(job.job_state, "pending")
        self.assertEqual(job.printer_id, self.printer)
        with mock.patch.object(
            PrintingJob, "_websocket_finished", autospec=True
        ) as finished:
            result = self._report(
                "other", job_uuid=job.websocket_uuid, state="completed"
            )
            self.assertIn("error", result)
            self.assertEqual(job.job_state, "pending")
            self._report(
                "agent",
                job_uuid=job.websocket_uuid,
                state="processing",
                cups_job_id=12,
            )
            self.assertEqual(job.job_state, "processing")
            self.assertEqual(job.job_id_cups, 12)
            self.assertTrue(job.time_at_processing)
            finished.assert_not_called()
            self._report(
                "agent",
                job_uuid=job.websocket_uuid,
                state="completed",
                reason="job-completed-successfully",
            )
            self._report("agent", job_uuid=job.websocket_uuid, state="completed")
        self.assertEqual(job.job_state, "completed")
        self.assertEqual(job.job_state_reason, "job-completed-successfully")
        self.assertTrue(job.time_at_completed)
        finished.assert_called_once()
        self.assertEqual(finished.call_args.args[0], job)

    def test_unknown_state_is_refused(self):
        job = self._send()
        result = self._report("agent", job_uuid=job.websocket_uuid, state="printed")
        self.assertIn("error", result)
        self.assertEqual(job.job_state, "pending")
