# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import errno
import logging
import os
from tempfile import mkstemp

from odoo import models, fields, api


_logger = logging.getLogger(__name__)

try:
    import cups
except ImportError:
    _logger.debug('Cannot `import cups`.')


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
    tray_ids = fields.One2many(comodel_name='printing.tray',
                               inverse_name='printer_id',
                               string='Paper Sources')

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
        printer_uri = cups_printer['printer-uri-supported']
        printer_system_name = printer_uri[printer_uri.rfind('/') + 1:]
        ppd_info = cups_connection.getPPD3(printer_system_name)
        ppd_path = ppd_info[2]
        if not ppd_path:
            return vals

        ppd = cups.PPD(ppd_path)
        option = ppd.findOption('InputSlot')
        try:
            os.unlink(ppd_path)
        except OSError as err:
            # ENOENT means No such file or directory
            # The file has already been deleted, we can continue the update
            if err.errno != errno.ENOENT:
                raise
        if not option:
            return vals

        vals['tray_ids'] = []
        cups_trays = {
            tray_option['choice']: tray_option['text']
            for tray_option in option.choices
        }

        # Add new trays
        vals['tray_ids'].extend([
            (0, 0, {'name': text, 'system_name': choice})
            for choice, text in cups_trays.items()
            if choice not in self.tray_ids.mapped('system_name')
        ])

        # Remove deleted trays
        vals['tray_ids'].extend([
            (2, tray.id)
            for tray in self.tray_ids.filtered(
                lambda record: record.system_name not in cups_trays.keys())
        ])
        return vals

    @api.multi
    def print_document(self, report, content, **print_opts):
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
            file_name, report=report, **print_opts)

    @staticmethod
    def _set_option_doc_format(report, value):
        return {'raw': 'True'} if value == 'raw' else {}

    # Backwards compatibility of builtin used as kwarg
    _set_option_format = _set_option_doc_format

    @api.multi
    def _set_option_tray(self, report, value):
        """Note we use self here as some older PPD use tray
        rather than InputSlot so we may need to query printer in override"""
        return {'InputSlot': str(value)} if value else {}

    @staticmethod
    def _set_option_noop(report, value):
        return {}

    _set_option_action = _set_option_noop
    _set_option_printer = _set_option_noop

    @api.multi
    def print_options(self, report=None, **print_opts):
        options = {}
        for option, value in print_opts.items():
            try:
                options.update(getattr(
                    self, '_set_option_%s' % option)(report, value))
            except AttributeError:
                options[option] = str(value)
        return options

    @api.multi
    def print_file(self, file_name, report=None, **print_opts):
        """ Print a file """
        self.ensure_one()
        connection = self.server_id._open_connection(raise_on_error=True)
        options = self.print_options(report=report, **print_opts)

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
        default_printers.unset_default()
        self.write({'default': True})
        return True

    @api.multi
    def unset_default(self):
        self.write({'default': False})
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
