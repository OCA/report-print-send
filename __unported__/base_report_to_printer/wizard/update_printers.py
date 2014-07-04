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


class printing_printer_update_wizard(orm.TransientModel):
    _name = "printing.printer.update.wizard"

    _columns = {
        }

    def action_cancel(self, cr, uid, ids, context=None):
        return {}

    def action_ok(self, cr, uid, ids, context=None):
        # Update Printers
        try:
            connection = cups.Connection()
            printers = connection.getPrinters()
        except:
            return {}

        ids = self.pool.get('printing.printer').search(cr, uid, [('system_name','in',printers.keys())], context=context)
        for printer in self.pool.get('printing.printer').browse(cr, uid, ids, context=context):
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


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
