# -*- coding: utf-8 -*-
# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PrintingJob(models.Model):
    _name = 'printing.job'
    _description = 'Printing Job'
    _order = 'job_id_cups DESC'

    name = fields.Char(help='Job name.')
    active = fields.Boolean(
        default=True, help='Unchecked if the job is purged from cups.')
    job_id_cups = fields.Integer(
        string='Job ID', required=True,
        help='CUPS id for this job.')
    server_id = fields.Many2one(
        comodel_name='printing.server', string='Server',
        related='printer_id.server_id', store=True,
        help='Server which hosts this job.')
    printer_id = fields.Many2one(
        comodel_name='printing.printer', string='Printer', required=True,
        ondelete='cascade', help='Printer used for this job.')
    job_media_progress = fields.Integer(
        string='Media Progress', required=True,
        help='Percentage of progress for this job.')
    time_at_creation = fields.Datetime(
        required=True, help='Date and time of creation for this job.')
    time_at_processing = fields.Datetime(
        help='Date and time of process for this job.')
    time_at_completed = fields.Datetime(
        help='Date and time of completion for this job.')
    job_state = fields.Selection(selection=[
        ('pending', 'Pending'),
        ('pending held', 'Pending Held'),
        ('processing', 'Processing'),
        ('processing stopped', 'Processing Stopped'),
        ('canceled', 'Canceled'),
        ('aborted', 'Aborted'),
        ('completed', 'Completed'),
        ('unknown', 'Unknown'),
    ], string='State', help='Current state of the job.')
    job_state_reason = fields.Selection(selection=[
        ('none', 'No reason'),
        ('aborted-by-system', 'Aborted by the system'),
        ('compression-error', 'Error in the compressed data'),
        ('document-access-error', 'The URI cannot be accessed'),
        ('document-format-error', 'Error in the document'),
        ('job-canceled-at-device', 'Cancelled at the device'),
        ('job-canceled-by-operator', 'Cancelled by the printer operator'),
        ('job-canceled-by-user', 'Cancelled by the user'),
        ('job-completed-successfully', 'Completed successfully'),
        ('job-completed-with-errors', 'Completed with some errors'),
        ('job-completed(with-warnings', 'Completed with some warnings'),
        ('job-data-insufficient', 'No data has been received'),
        ('job-hold-until-specified', 'Currently held'),
        ('job-incoming', 'Files are currently being received'),
        ('job-interpreting', 'Currently being interpreted'),
        ('job-outgoing', 'Currently being sent to the printer'),
        ('job-printing', 'Currently printing'),
        ('job-queued', 'Queued for printing'),
        ('job-queued-for-marker', 'Printer needs ink/marker/toner'),
        ('job-restartable', 'Can be restarted'),
        ('job-transforming', 'Being transformed into a different format'),
        ('printer-stopped', 'Printer is stopped'),
        ('printer-stopped-partly',
         'Printer state reason set to \'stopped-partly\''),
        ('processing-to-stop-point',
         'Cancelled, but printing already processed pages'),
        ('queued-in-device', 'Queued at the output device'),
        ('resources-are-not-ready',
         'Resources not available to print the job'),
        ('service-off-line', 'Held because the printer is offline'),
        ('submission-interrupted', 'Files were not received in full'),
        ('unsupported-compression', 'Compressed using an unknown algorithm'),
        ('unsupported-document-format', 'Unsupported format'),
    ], string='State Reason', help='Reason for the current job state.')

    _sql_constraints = [
        ('job_id_cups_unique', 'UNIQUE(job_id_cups, server_id)',
         'The id of the job must be unique per server !'),
    ]

    @api.multi
    def action_cancel(self):
        self.ensure_one()
        return self.cancel()

    @api.multi
    def cancel(self, purge_job=False):
        for job in self:
            connection = job.server_id._open_connection()
            if not connection:
                continue

            connection.cancelJob(job.job_id_cups, purge_job=purge_job)

        # Update jobs' states info Odoo
        self.mapped('server_id').update_jobs(
            which='all', first_job_id=job.job_id_cups)

        return True
