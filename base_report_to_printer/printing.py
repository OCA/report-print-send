# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
#    Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2013 Camptocamp (<http://www.camptocamp.com>)
#    All Rights Reserved
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
import time

import cups
import os
from threading import Thread
from threading import Lock
from tempfile import mkstemp
import logging

from openerp import pooler
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools.config import config

_logger = logging.getLogger(__name__)
CUPS_HOST = config.get('cups_host', 'localhost')
CUPS_PORT = int(config.get('cups_port', 631))  # config.get returns a string


class printing_printer(orm.Model):

    """
    Printers
    """
    _name = "printing.printer"
    _description = "Printer"

    _columns = {
        'name': fields.char(
            'Name',
            size=64,
            required=True,
            select="1"),
        'system_name': fields.char(
            'System Name',
            size=64,
            required=True,
            select="1"),
        'default': fields.boolean(
            'Default Printer',
            readonly=True),
        'status': fields.selection(
            [('unavailable', 'Unavailable'),
             ('printing', 'Printing'),
             ('unknown', 'Unknown'),
             ('available', 'Available'),
             ('error', 'Error'),
             ('server-error', 'Server Error')],
            'Status', required=True, readonly=True),
        'status_message': fields.char(
            'Status Message',
            size=500,
            readonly=True),
        'model': fields.char(
            'Model',
            size=500,
            readonly=True),
        'location': fields.char(
            'Location',
            size=500,
            readonly=True),
        'uri': fields.char(
            'URI',
            size=500,
            readonly=True),
    }

    _order = "name"

    _defaults = {
        'default': lambda *a: False,
        'status': lambda *a: 'unknown',
    }

    def __init__(self, pool, cr):
        super(printing_printer, self).__init__(pool, cr)
        self.lock = Lock()
        self.last_update = None
        self.updating = False

    def update_printers_status(self, db_name, uid, context=None):
        db, pool = pooler.get_db_and_pool(db_name)
        cr = db.cursor()

        try:
            connection = cups.Connection(CUPS_HOST, CUPS_PORT)
            printers = connection.getPrinters()
            server_error = False
        except:
            server_error = True

        mapping = {
            3: 'available',
            4: 'printing',
            5: 'error'
        }

        if context is None:
            context = {}
        try:
            # Skip update to avoid the thread being created again
            ctx = context.copy()
            ctx['skip_update'] = True
            ids = self.search(cr, uid, [], context=ctx)
            for printer in self.browse(cr, uid, ids, context=ctx):
                vals = {}
                if server_error:
                    status = 'server-error'
                elif printer.system_name in printers:
                    info = printers[printer.system_name]
                    status = mapping.get(info['printer-state'], 'unknown')
                    vals = {
                        'model': info.get('printer-make-and-model', False),
                        'location': info.get('printer-location', False),
                        'uri': info.get('device-uri', False),
                    }
                else:
                    status = 'unavailable'

                vals['status'] = status
                self.write(cr, uid, [printer.id], vals, context=context)
            cr.commit()
        except:
            cr.rollback()
            raise
        finally:
            cr.close()
        with self.lock:
            self.updating = False
            self.last_update = time.time()

    def start_printer_update(self, cr, uid, context):
        self.lock.acquire()
        if self.updating:
            self.lock.release()
            return
        self.updating = True
        self.lock.release()
        thread = Thread(target=self.update_printers_status,
                        args=(cr.dbname, uid, context.copy()))
        thread.start()

    def update(self, cr, uid, context=None):
        """Update printer status if current status is more than 10s old."""
        # We won't acquire locks - we're only assigning from immutable data
        if not context or 'skip_update' in context:
            return True
        last_update = self.last_update
        now = time.time()
        # Only update printer status if current status is more than
        # 10 seconds old.
        if not last_update or now - last_update > 10:
            self.start_printer_update(cr, uid, context)
            # Wait up to five seconds for printer status update
            for _dummy in range(0, 5):
                time.sleep(1)
                if not self.updating:
                    break
        return True

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
               context=None, count=False):
        self.update(cr, uid, context)
        return super(printing_printer, self
                     ).search(cr, uid, args, offset,
                              limit, order, context, count)

    def read(self, cr, uid, ids, fields=None, context=None,
             load='_classic_read'):
        self.update(cr, uid, context)
        return super(printing_printer, self
                     ).read(cr, uid, ids, fields, context, load)

    def browse(self, cr, uid, ids, context=None):
        self.update(cr, uid, context)
        return super(printing_printer, self).browse(cr, uid, ids, context)

    def print_options(
            self, cr, uid, ids, report, format, copies=1, context=None):
        """ Hook to set print options """
        options = {}
        if format == 'raw':
            options['raw'] = 'True'
        if copies > 1:
            options['copies'] = str(copies)
        return options

    def print_document(
            self, cr, uid, ids, report, content, format, copies=1,
            context=None):
        """ Print a file

        Format could be pdf, qweb-pdf, raw, ...

        """
        assert len(ids) == 1, 'Only 1 ID allowed'
        printer = self.browse(cr, uid, ids[0], context=context)
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

        options = self.print_options(
            cr, uid, ids, report, format, copies, context=context)

        _logger.debug(
            'Sending job to CUPS printer %s on %s'
            % (printer.system_name, CUPS_HOST))
        connection.printFile(printer.system_name,
                             file_name,
                             file_name,
                             options=options)
        _logger.info("Printing job: '%s' on %s" % (file_name, CUPS_HOST))
        return True

    def set_default(self, cr, uid, ids, context):
        if not ids:
            return
        default_ids = self.search(cr, uid, [('default', '=', True)])
        self.write(cr, uid, default_ids, {'default': False}, context)
        self.write(cr, uid, ids[0], {'default': True}, context)
        return True

    def get_default(self, cr, uid, context):
        printer_ids = self.search(cr, uid, [('default', '=', True)])
        if printer_ids:
            return printer_ids[0]
        return False


#
# Actions
#

def _available_action_types(self, cr, uid, context=None):
    return [
        ('server', _('Send to Printer')),
        ('client', _('Send to Client')),
        ('user_default', _("Use user's defaults")),
    ]


class printing_action(orm.Model):
    _name = 'printing.action'
    _description = 'Print Job Action'

    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'type': fields.selection(_available_action_types, 'Type',
                                 required=True),
    }
