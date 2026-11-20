# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import uuid

from odoo import api, fields, models

FINAL_STATES = ("completed", "canceled", "aborted")


class PrintingJob(models.Model):
    _inherit = "printing.job"

    websocket_uuid = fields.Char(
        string="WebSocket Job", index=True, copy=False, readonly=True
    )

    @api.model
    def _websocket_create(self, printer, name):
        return self.sudo().create(
            {
                "name": name,
                "printer_id": printer.id,
                "job_id_cups": 0,
                "job_media_progress": 0,
                "job_state": "pending",
                "time_at_creation": fields.Datetime.now(),
                "websocket_uuid": str(uuid.uuid4()),
            }
        )

    def _websocket_update(self, state, cups_job_id=None, reason=None):
        """The print client of the printer reports the CUPS state of the job."""
        self.ensure_one()
        reasons = dict(self._fields["job_state_reason"].selection)
        vals = {"job_state": state}
        if cups_job_id:
            vals["job_id_cups"] = cups_job_id
        if reason in reasons:
            vals["job_state_reason"] = reason
        if state == "processing" and not self.time_at_processing:
            vals["time_at_processing"] = fields.Datetime.now()
        finished = state in FINAL_STATES and self.job_state not in FINAL_STATES
        if state in FINAL_STATES:
            vals["time_at_completed"] = fields.Datetime.now()
        self.write(vals)
        if finished:
            self._websocket_finished()

    def _websocket_finished(self):
        """Hook: the job left the CUPS queue of the print client, in
        `job_state` completed, canceled or aborted."""
