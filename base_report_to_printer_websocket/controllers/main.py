# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from werkzeug.exceptions import BadRequest, NotFound

from odoo import http
from odoo.http import request

REPORTED_STATES = ("processing", "completed", "canceled", "aborted")


class PrintingWebsocketController(http.Controller):
    @http.route("/printing/websocket/job/state", type="json", auth="user")
    def job_state(self, job_uuid, state, cups_job_id=None, reason=None):
        """The print client reports the CUPS state of a job it received."""
        if state not in REPORTED_STATES or not isinstance(job_uuid, str):
            raise BadRequest()
        job = (
            request.env["printing.job"]
            .sudo()
            .search(
                [
                    ("websocket_uuid", "=", job_uuid),
                    ("printer_id.websocket_user_id", "=", request.env.uid),
                ],
                limit=1,
            )
        )
        if not job:
            raise NotFound()
        job._websocket_update(
            state,
            cups_job_id=cups_job_id if isinstance(cups_job_id, int) else None,
            reason=reason,
        )
        return True
