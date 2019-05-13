# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


try:
    import cups
except ImportError:
    _logger.debug('Cannot `import cups`.')


class PrintingServer(models.Model):
    _name = 'printing.server'
    _description = 'Printing server'

    name = fields.Char(
        default='Localhost', required=True, help='Name of the server.')
    address = fields.Char(
        default='localhost', required=True,
        help='IP address or hostname of the server')
    port = fields.Integer(
        default=631, required=True, help='Port of the server.')
    active = fields.Boolean(
        default=True, help='If checked, this server is useable.')
    printer_ids = fields.One2many(
        comodel_name='printing.printer', inverse_name='server_id',
        string='Printers List',
        help='List of printers available on this server.')

    @api.multi
    def _open_connection(self, raise_on_error=False):
        self.ensure_one()
        connection = False
        try:
            connection = cups.Connection(host=self.address, port=self.port)
        except:
            message = _("Failed to connect to the CUPS server on %s:%s. "
                        "Check that the CUPS server is running and that "
                        "you can reach it from the Odoo server.") % (
                            self.address, self.port)
            _logger.warning(message)
            if raise_on_error:
                raise exceptions.UserError(message)

        return connection

    @api.multi
    def action_update_printers(self):
        return self.update_printers()

    @api.multi
    def update_printers(self, domain=None, raise_on_error=False):
        if domain is None:
            domain = []

        servers = self
        if not self:
            servers = self.search(domain)

        res = True
        for server in servers:
            connection = server._open_connection(raise_on_error=raise_on_error)
            if not connection:
                server.printer_ids.write({'status': 'server-error'})
                res = False
                continue

            # Update Printers
            printers = connection.getPrinters()
            existing_printers = dict([
                (printer.system_name, printer)
                for printer in server.printer_ids
            ])
            updated_printers = []
            for name, printer_info in printers.items():
                printer = self.env['printing.printer']
                if name in existing_printers:
                    printer = existing_printers[name]

                printer_values = printer._prepare_update_from_cups(
                    connection, printer_info)
                printer_values.update(
                    system_name=name,
                    server_id=server.id,
                )
                updated_printers.append(name)
                if not printer:
                    printer.create(printer_values)
                else:
                    printer.write(printer_values)

            # Set printers not found as unavailable
            server.printer_ids.filtered(
                lambda record: record.system_name not in updated_printers)\
                .write({'status': 'unavailable'})

        return res

    def action_update_jobs(self):
        if not self:
            self = self.search([])
        return self.update_jobs()

    @api.multi
    def update_jobs(self, which='all', first_job_id=-1):
        job_obj = self.env['printing.job']
        printer_obj = self.env['printing.printer']

        mapping = {
            3: 'pending',
            4: 'pending held',
            5: 'processing',
            6: 'processing stopped',
            7: 'canceled',
            8: 'aborted',
            9: 'completed',
        }

        # Update printers list, to ensure that jobs printers will be in Odoo
        self.update_printers()

        for server in self:
            connection = server._open_connection()
            if not connection:
                continue

            # Retrieve asked job data
            jobs_data = connection.getJobs(
                which_jobs=which, first_job_id=first_job_id,
                requested_attributes=[
                    'job-name',
                    'job-id',
                    'printer-uri',
                    'job-media-progress',
                    'time-at-creation',
                    'job-state',
                    'job-state-reasons',
                    'time-at-processing',
                    'time-at-completed',
                ])

            # Retrieve known uncompleted jobs data to update them
            if which == 'not-completed':
                oldest_uncompleted_job = job_obj.search([
                    ('job_state', 'not in', (
                        'canceled',
                        'aborted',
                        'completed',
                    )),
                ], limit=1, order='job_id_cups')
                if oldest_uncompleted_job:
                    jobs_data.update(connection.getJobs(
                        which_jobs='completed',
                        first_job_id=oldest_uncompleted_job.job_id_cups,
                        requested_attributes=[
                            'job-name',
                            'job-id',
                            'printer-uri',
                            'job-media-progress',
                            'time-at-creation',
                            'job-state',
                            'job-state-reasons',
                            'time-at-processing',
                            'time-at-completed',
                        ]))

            all_cups_job_ids = set()
            for cups_job_id, job_data in jobs_data.items():
                all_cups_job_ids.add(cups_job_id)
                jobs = job_obj.with_context(active_test=False).search([
                    ('job_id_cups', '=', cups_job_id),
                    ('server_id', '=', server.id),
                ])
                job_values = {
                    'name': job_data.get('job-name', ''),
                    'active': True,
                    'job_id_cups': cups_job_id,
                    'job_media_progress': job_data.get(
                        'job-media-progress', False),
                    'job_state': mapping.get(
                        job_data.get('job-state'), 'unknown'),
                    'job_state_reason': job_data.get('job-state-reasons', ''),
                    'time_at_creation': fields.Datetime.to_string(
                        datetime.fromtimestamp(job_data.get(
                            'time-at-creation', False))),
                    'time_at_processing': job_data.get(
                        'time-at-processing', False) and
                    fields.Datetime.to_string(datetime.fromtimestamp(
                        job_data.get('time-at-processing', False))),
                    'time_at_completed': job_data.get(
                        'time-at-completed', False) and
                    fields.Datetime.to_string(datetime.fromtimestamp(
                        job_data.get('time-at-completed', False))),
                }

                # Search for the printer in Odoo
                printer_uri = job_data['printer-uri']
                printer_system_name = printer_uri[printer_uri.rfind('/') + 1:]
                printer = printer_obj.search([
                    ('server_id', '=', server.id),
                    ('system_name', '=', printer_system_name),
                ], limit=1)
                # CUPS retains jobs for disconnected printers and also may
                # leak jobs data for unshared printers, therefore we just
                # discard here if not printer found
                if not printer:
                    continue
                job_values['printer_id'] = printer.id

                if jobs:
                    jobs.write(job_values)
                else:
                    job_obj.create(job_values)

            # Deactive purged jobs
            if which == 'all' and first_job_id == -1:
                purged_jobs = job_obj.search([
                    ('job_id_cups', 'not in', list(all_cups_job_ids)),
                ])
                purged_jobs.write({'active': False})

        return True
