# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
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

import cups

from openerp.osv import orm
from openerp.tools.config import config

CUPS_HOST = config.get('cups_host', 'localhost')
CUPS_PORT = int(config.get('cups_port', 631))  # config.get returns a string


class printing_printer_update_wizard(orm.TransientModel):
    _name = "printing.printer.update.wizard"

    def action_cancel(self, cr, uid, ids, context=None):
        return {}

    def action_ok(self, cr, uid, ids, context=None):
        # Update Printers
        printer_obj = self.pool['printing.printer']
        try:
            connection = cups.Connection(CUPS_HOST, CUPS_PORT)
            printers = connection.getPrinters()
        except:
            return {}

        ids = printer_obj.search(
            cr, uid, [('system_name', 'in', printers.keys())], context=context)
        for printer in printer_obj.browse(cr, uid, ids, context=context):
            del printers[printer.system_name]

        for name in printers:
            printer = printers[name]
            self.pool.get('printing.printer').create(cr, uid, {
                'name': printer['printer-info'],
                'system_name': name,
                'model': printer.get('printer-make-and-model', False),
                'location': printer.get('printer-location', False),
                'uri': printer.get('device-uri', False),
            }, context)

        return {
            'name': 'Printers',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'printing.printer',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
