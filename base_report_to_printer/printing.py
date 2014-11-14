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
import time

import cups

from threading import Thread
from threading import Lock

from openerp import models, fields, api, sql_db


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
    uri = fields.Char(readonly=True)

    def __init__(self, pool, cr):
        super(PrintingPrinter, self).__init__(pool, cr)
        self.lock = Lock()
        self.last_update = None
        self.updating = False

    @api.model
    def update_printers_status(self):
        cr = sql_db.db_connect(self.env.cr.dbname).cursor()
        uid, context = self.env.uid, self.env.context
        with api.Environment.manage():
            self.env = api.Environment(cr, uid, context)
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

            try:
                # Skip update to avoid the thread being created again
                env = self.env.with_context(skip_update=True)
                printer_recs = env.search([])
                for printer in printer_recs:
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
                    printer.write(vals)
                self.env.cr.commit()
            except:
                self.env.cr.rollback()
                raise
            finally:
                self.env.cr.close()
            with self.lock:
                self.updating = False
                self.last_update = time.time()

    @api.model
    def start_printer_update(self):
        self.lock.acquire()
        if self.updating:
            self.lock.release()
            return
        self.updating = True
        self.lock.release()
        thread = Thread(target=self.update_printers_status, args=())
        thread.start()

    @api.model
    def update(self):
        """Update printer status if current status is more than 10s old."""
        # We won't acquire locks - we're only assigning from immutable data
        if not self.env.context or 'skip_update' in self.env.context:
            return True
        last_update = self.last_update
        now = time.time()
        # Only update printer status if current status is more than 10
        # seconds old.
        if not last_update or now - last_update > 10:
            self.start_printer_update()
            # Wait up to five seconds for printer status update
            for _dummy in range(0, 5):
                time.sleep(1)
                if not self.updating:
                    break
        return True

    @api.returns('self')
    def search(self, cr, user, args, offset=0, limit=None, order=None,
               context=None, count=False):
        self.update()
        _super = super(PrintingPrinter, self)
        return _super.search(cr, user, args, offset=offset, limit=limit,
                             order=order, context=context, count=count)

    @api.v7
    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        # https://github.com/odoo/odoo/issues/3644
        # self.update(cr, user, context=context)
        _super = super(PrintingPrinter, self)
        return _super.read(cr, user, ids, fields=fields, context=context,
                           load=load)

    @api.v8
    def read(self, fields=None, load='_classic_read'):
        self.update()
        return super(PrintingPrinter, self).read(fields=fields, load=load)

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
