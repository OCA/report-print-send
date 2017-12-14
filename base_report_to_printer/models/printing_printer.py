# -*- coding: utf-8 -*-
# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import os
from tempfile import mkstemp

from odoo import models, fields, api


_logger = logging.getLogger(__name__)


class PrintingPrinter(models.Model):
    """
    Printers
    """

    _name = 'printing.printer'
    _description = 'Printer'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    server_id = fields.Many2one(
        comodel_name='printing.server', string='Server', required=True,
        help='Server used to access this printer.')
    job_ids = fields.One2many(
        comodel_name='printing.job', inverse_name='printer_id', string='Jobs',
        help='Jobs printed on this printer.')
    system_name = fields.Char(required=True, index=True)
    default = fields.Boolean(readonly=True)
    status = fields.Selection(
        selection=[
            ('unavailable', 'Unavailable'),
            ('printing', 'Printing'),
            ('unknown', 'Unknown'),
            ('available', 'Available'),
            ('error', 'Error'),
            ('server-error', 'Server Error'),
        ],
        required=True,
        readonly=True,
        default='unknown')
    status_message = fields.Char(readonly=True)
    model = fields.Char(readonly=True)
    location = fields.Char(readonly=True)
    uri = fields.Char(string='URI', readonly=True)

    @api.multi
    def _prepare_update_from_cups(self, cups_connection, cups_printer):
        mapping = {
            3: 'available',
            4: 'printing',
            5: 'error'
        }
        vals = {
            'name': cups_printer['printer-info'],
            'model': cups_printer.get('printer-make-and-model', False),
            'location': cups_printer.get('printer-location', False),
            'uri': cups_printer.get('device-uri', False),
            'status': mapping.get(cups_printer.get(
                'printer-state'), 'unknown'),
            'status_message': cups_printer.get('printer-state-message', ''),
        }
        return vals

    @api.multi
    def print_options(self, report=None, format=None, copies=1):
        """ Hook to set print options """
        options = {}
        if format == 'raw':
            options['raw'] = 'True'
        if copies > 1:
            options['copies'] = str(copies)
        return options

    @api.multi
    def print_document(self, report, content, format, copies=1):
        """ Print a file

        Format could be pdf, qweb-pdf, raw, ...

        """
        self.ensure_one()
        fd, file_name = mkstemp()
        try:
            os.write(fd, content)
        finally:
            os.close(fd)

        return self.print_file(
            file_name, report=report, copies=copies, format=format)

    @api.multi
    def print_file(self, file_name, report=None, copies=1, format=None):
        """ Print a file """
        self.ensure_one()

        connection = self.server_id._open_connection(raise_on_error=True)
        options = self.print_options(
            report=report, format=format, copies=copies)

        _logger.debug(
            'Sending job to CUPS printer %s on %s'
            % (self.system_name, self.server_id.address))
        connection.printFile(self.system_name,
                             file_name,
                             file_name,
                             options=options)
        _logger.info("Printing job: '%s' on %s" % (
            file_name,
            self.server_id.address,
        ))
        return True

    @api.multi
    def set_default(self):
        if not self:
            return
        self.ensure_one()
        default_printers = self.search([('default', '=', True)])
        default_printers.write({'default': False})
        self.write({'default': True})
        return True

    @api.multi
    def get_default(self):
        return self.search([('default', '=', True)], limit=1)

    @api.multi
    def action_cancel_all_jobs(self):
        self.ensure_one()
        return self.cancel_all_jobs()

    @api.multi
    def cancel_all_jobs(self, purge_jobs=False):
        for printer in self:
            connection = printer.server_id._open_connection()
            connection.cancelAllJobs(
                name=printer.system_name, purge_jobs=purge_jobs)

        # Update jobs' states into Odoo
        self.mapped('server_id').update_jobs(which='completed')

        return True

    @api.multi
    def enable(self):
        for printer in self:
            connection = printer.server_id._open_connection()
            connection.enablePrinter(printer.system_name)

        # Update printers' stats into Odoo
        self.mapped('server_id').update_printers()

        return True

    @api.multi
    def disable(self):
        for printer in self:
            connection = printer.server_id._open_connection()
            connection.disablePrinter(printer.system_name)

        # Update printers' stats into Odoo
        self.mapped('server_id').update_printers()

        return True
