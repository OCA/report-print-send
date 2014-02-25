# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import cups
from cups import PPD

from openerp import pooler
from openerp.osv import orm, fields


class Printer(orm.Model):

    _inherit = 'printing.printer'

    _columns = {
        'tray_ids': fields.one2many('printing.tray', 'printer_id', 'Paper Sources'),
        }

    def _update_tray_option(self, db_name, uid, printer, context=None):
        """
        Create missing tray for a printer
        """
        db, pool = pooler.get_db_and_pool(db_name)
        cr = db.cursor()
        tray_obj = pool.get('printing.tray')
        # get printers options from a PPD file
        try:
            connection = cups.Connection()
            ppd_file_path = connection.getPPD3(printer.system_name)
        except:
            return
        if not ppd_file_path[2]:
            return
        ppd = PPD(ppd_file_path[2])
        option = ppd.findOption('InputSlot')
        if not option:
            return
        try:
            for tray_opt in option.choices:
                if tray_opt['choice'] not in [t.system_name for t in printer.tray_ids]:
                    tray_vals = {
                        'name': tray_opt['text'],
                        'system_name': tray_opt['choice'],
                        'printer_id': printer.id,
                        }

                    tray_obj.create(cr, uid, tray_vals, context=context)
            cr.commit()
        except:
            cr.rollback()
            raise
        finally:
            cr.close()
        return True

    def update_printers_status(self, db_name, uid, context=None):
        """
        Add creation of tray if no tray are defined
        """
        db, pool = pooler.get_db_and_pool(db_name)
        cr = db.cursor()
        res = super(Printer, self).update_printers_status(db_name, uid, context=context)
        try:
            connection = cups.Connection()
            printers = connection.getPrinters()
            server_error = False
        except:
            server_error = True

        printer_ids = self.search(cr, uid, [('system_name', 'in', printers.keys())], context=context)
        if server_error:
            vals = {'status': 'server_error'}
            self.write(cr, uid, printer_ids, vals, context=context)
            return res

        printer_list = self.browse(cr, uid, printer_ids, context=context)

        for printer in printer_list:
            # XXX we consider config of printer won't change
            if not printer.tray_ids:
                self._update_tray_option(db_name, uid, printer, context=context)
        return res
