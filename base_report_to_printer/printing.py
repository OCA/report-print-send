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

from contextlib import contextmanager
from datetime import datetime
from tempfile import mkstemp
from threading import Thread

import cups
import psycopg2

from openerp import models, fields, api, sql_db

_logger = logging.getLogger(__name__)

POLL_INTERVAL = 10  # seconds


class PrintingPrinterPolling(models.Model):
    """ Keep the last update time of printers update.

    This table will contain only 1 row, with the last time we checked
    the list of printers from cups.

    The table is locked before an update so 2 processes won't be able
    to do the update at the same time.
    """
    _name = 'printing.printer.polling'
    _description = 'Printers Polling'

    last_update = fields.Datetime()

    @api.model
    def find_unique_record(self):
        polling = self.search([], limit=1)
        return polling

    @api.model
    def find_or_create_unique_record(self):
        polling = self.find_unique_record()
        if polling:
            return polling
        cr = self.env.cr
        try:
            # Will be released at the end of the transaction.  Locks the
            # full table for insert/update because we must have only 1
            # record in this table, so we prevent 2 processes to create
            # each one one line at the same time.
            cr.execute("LOCK TABLE %s IN SHARE ROW EXCLUSIVE MODE NOWAIT" %
                       self._table, log_exceptions=False)
        except psycopg2.OperationalError as err:
            # the lock could not be acquired, already running
            if err.pgcode == '55P03':
                _logger.debug('Another process/thread is already '
                              'creating the polling record.')
                return self.browse()
            else:
                raise
        return self.create({'last_update': False})

    @api.multi
    def lock(self):
        """ Lock the polling record

        Lock the record in the database so we can prevent concurrent
        processes to update at the same time.

        The lock is released either on commit or rollback of the
        transaction.

        Returns if the record has been locked or not.
        """
        self.ensure_one()
        cr = self.env.cr
        sql = ("SELECT id FROM %s WHERE id = %%s FOR UPDATE NOWAIT" %
               self._table)
        try:
            cr.execute(sql, (self.id, ), log_exceptions=False)
        except psycopg2.OperationalError as err:
            # the lock could not be acquired, already running
            if err.pgcode == '55P03':
                _logger.debug('Another process/thread is already '
                              'updating the printers list.')
                return False
            if err.pgcode == '40001':
                _logger.debug('could not serialize access due to '
                              'concurrent update')
                return False
            else:
                raise
        return True

    @contextmanager
    @api.model
    def start_update(self):
        locked = False
        polling = self.find_or_create_unique_record()
        if polling:
            if polling.lock():
                locked = True
        yield locked
        if locked:
            polling.write({'last_update': fields.Datetime.now()})

    @api.model
    def need_update(self):
        polling = self.find_unique_record()
        if not polling:
            return True
        last_update = polling.last_update
        if last_update:
            last_update = fields.Datetime.from_string(last_update)
        now = datetime.now()
        # Only update printer status if current status is more than 10
        # seconds old.
        if not last_update or (now - last_update).seconds >= POLL_INTERVAL:
            return True
        return False

    @api.model
    def update_printers_status(self):
        cr = sql_db.db_connect(self.env.cr.dbname).cursor()
        uid, context = self.env.uid, self.env.context
        with api.Environment.manage():
            try:
                self.env = api.Environment(cr, uid, context)
                printer_obj = self.env['printing.printer']
                printer_obj = printer_obj.with_context(skip_update=True)
                with self.start_update() as locked:
                    if not locked:
                        return  # could not obtain lock
                    try:
                        connection = cups.Connection()
                        printers = connection.getPrinters()
                        server_error = False
                    except:
                        server_error = True

                    mapping = {
                        3: 'available',
                        4: 'printing',
                        5: 'error'
                    }

                    # Skip update to avoid the thread being created again
                    printer_recs = printer_obj.search([])
                    for printer in printer_recs:
                        vals = {}
                        if server_error:
                            status = 'server-error'
                        elif printer.system_name in printers:
                            info = printers[printer.system_name]
                            status = mapping.get(info['printer-state'],
                                                 'unknown')
                            vals = {
                                'model': info.get('printer-make-and-model',
                                                  False),
                                'location': info.get('printer-location',
                                                     False),
                                'uri': info.get('device-uri',
                                                False),
                            }
                        else:
                            status = 'unavailable'

                        vals['status'] = status
                        printer.write(vals)

                self.env.cr.commit()
            except:
                self.env.cr.rollback()
                raise
            finally:
                self.env.cr.close()


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

    @api.multi
    def print_options(self, format):
        """ Hook to set print options """
        options = {}
        if format == 'raw':
            options['raw'] = True
        return options

    @api.multi
    def print_document(self, content, format):
        """ Print a file

        Format could be pdf, qweb-pdf, raw, ...

        """
        self.ensure_one()
        fd, file_name = mkstemp()
        try:
            os.write(fd, content)
        finally:
            os.close(fd)
        connection = cups.Connection()

        options = self.print_options(format)

        connection.printFile(self.system_name,
                             file_name,
                             file_name,
                             options=options)
        _logger.info("Printing job: '%s'" % file_name)
        return True

    @api.model
    def start_printer_update(self):
        polling_obj = self.env['printing.printer.polling']
        thread = Thread(target=polling_obj.update_printers_status, args=())
        thread.start()

    @api.model
    def update(self):
        """Update printer status if current status is more than 10s old."""
        # We won't acquire locks - we're only assigning from immutable data
        if not self.env.context or 'skip_update' in self.env.context:
            return True
        polling_obj = self.env['printing.printer.polling']

        if polling_obj.need_update():
            self.start_printer_update()

        return True

    @api.v7
    def browse(self, cr, uid, arg=None, context=None):
        # https://github.com/odoo/odoo/issues/3644
        # self.update(cr, uid, context=context)
        _super = super(PrintingPrinter, self)
        return _super.browse(cr, uid, arg=arg, context=context)

    @api.v8
    def browse(self, arg=None):
        self.update()
        return super(PrintingPrinter, self).browse(arg=arg)

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
