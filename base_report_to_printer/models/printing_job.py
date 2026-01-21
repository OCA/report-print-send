# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class PrintingJob(models.Model):
    _name = "printing.job"
    _description = "Print Job"

    name = fields.Char(help="Job name.")
    printer_id = fields.Many2one(
        comodel_name="printing.printer",
        string="Printer",
        required=True,
        ondelete="cascade",
        help="Printer used for this job.",
    )
    time_at_creation = fields.Datetime(
        string="Creation Date",
        required=True,
        help="Date and time of creation of this job.",
    )
    time_at_processing = fields.Datetime(
        string="Processing Date", help="Date and time of process for this job."
    )
    time_at_completed = fields.Datetime(
        string="Completion Date", help="Date and time of completion for this job."
    )
    job_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("unknown", "Unknown"),
        ],
        string="State",
        help="Current state of the job.",
    )

    def action_cancel(self):
        self.ensure_one()
        return self.cancel()

    def cancel(self):
        return True
