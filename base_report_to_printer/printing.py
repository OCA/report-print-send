# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
#    Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
import os
from tempfile import mkstemp
import cups
from openerp import models, fields, api, _
from openerp.exceptions import Warning
from openerp.tools.config import config

_logger = logging.getLogger(__name__)
CUPS_HOST = config.get('cups_host', 'localhost')
CUPS_PORT = int(config.get('cups_port', 631))  # config.get returns a string


class PrintingPrinter(models.Model):
    """
    Printers
    """

    _name = 'printing.printer'
    _description = 'Printer'
    _order = 'name'

    name = fields.Char(required=True, select=True)
    system_name = fields.Char(required=True, select=True)
    default = fields.Boolean(readonly=True)
    status = fields.Selection([('unavailable', 'Unavailable'),
                               ('printing', 'Printing'),
                               ('unknown', 'Unknown'),
                               ('available', 'Available'),
                               ('error', 'Error'),
                               ('server-error', 'Server Error')],
                              required=True,
                              readonly=True,
                              default='unknown')
    status_message = fields.Char(readonly=True)
    model = fields.Char(readonly=True)
    location = fields.Char(readonly=True)
    uri = fields.Char(string='URI', readonly=True)

    @api.model
    def update_printers_status(self):
        printer_recs = self.search([])
        try:
            connection = cups.Connection(CUPS_HOST, CUPS_PORT)
            printers = connection.getPrinters()
        except:
            printer_recs.write({'status': 'server-error'})
        else:
            for printer in printer_recs:
                cups_printer = printers.get(printer.system_name)
                if cups_printer:
                    printer.update_from_cups(connection, cups_printer)
                else:
                    # not in cups list
                    printer.status = 'unavailable'
        return True

    @api.multi
    def _prepare_update_from_cups(self, cups_connection, cups_printer):
        mapping = {
            3: 'available',
            4: 'printing',
            5: 'error'
        }
        vals = {
            'model': cups_printer.get('printer-make-and-model', False),
            'location': cups_printer.get('printer-location', False),
            'uri': cups_printer.get('device-uri', False),
            'status': mapping.get(cups_printer['printer-state'], 'unknown'),
        }
        return vals

    @api.multi
    def update_from_cups(self, cups_connection, cups_printer):
        """ Update a printer from the information returned by cups.

        :param cups_connection: connection to CUPS, may be used when the
                                method is overriden (e.g. in printer_tray)
        :param cups_printer: dict of information returned by CUPS for the
                             current printer
        """
        self.ensure_one()
        vals = self._prepare_update_from_cups(cups_connection, cups_printer)
        if any(self[name] != value for name, value in vals.iteritems()):
            self.write(vals)

    @api.multi
    def print_options(self, report, format):
        """ Hook to set print options """
        options = {}
        if format == 'raw':
            options['raw'] = 'True'
        return options

    @api.multi
    def print_document(self, report, content, format):
        """ Print a file

        Format could be pdf, qweb-pdf, raw, ...

        """
        self.ensure_one()
        fd, file_name = mkstemp()
        try:
            os.write(fd, content)
        finally:
            os.close(fd)

        try:
            _logger.debug(
                'Starting to connect to CUPS on %s:%s'
                % (CUPS_HOST, CUPS_PORT))
            connection = cups.Connection(CUPS_HOST, CUPS_PORT)
            _logger.debug('Connection to CUPS successfull')
        except:
            raise Warning(
                _("Failed to connect to the CUPS server on %s:%s. "
                    "Check that the CUPS server is running and that "
                    "you can reach it from the Odoo server.")
                % (CUPS_HOST, CUPS_PORT))

        options = self.print_options(report, format)

        _logger.debug(
            'Sending job to CUPS printer %s on %s'
            % (self.system_name, CUPS_HOST))
        connection.printFile(self.system_name,
                             file_name,
                             file_name,
                             options=options)
        _logger.info("Printing job: '%s' on %s" % (file_name, CUPS_HOST))
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

#
# Actions
#


def _available_action_types(self):
    return [('server', 'Send to Printer'),
            ('client', 'Send to Client'),
            ('user_default', "Use user's defaults"),
            ]


class PrintingAction(models.Model):
    _name = 'printing.action'
    _description = 'Print Job Action'

    name = fields.Char(required=True)
    type = fields.Selection(_available_action_types, required=True)
