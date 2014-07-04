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
import base64

from openerp import pooler
from openerp.addons.base_calendar import base_calendar

class virtual_report_spool(base_calendar.virtual_report_spool):

    def exp_report(self, db, uid, object, ids, datas=None, context=None):
        res = super(virtual_report_spool, self).exp_report(db, uid, object, ids, datas, context)
        self._reports[res]['report_name'] = object
        return res

    def exp_report_get(self, db, uid, report_id):

        cr = pooler.get_db(db).cursor()
        try:
            pool = pooler.get_pool(cr.dbname)
            # First of all load report defaults: name, action and printer
            report_obj = pool.get('ir.actions.report.xml')
            report = report_obj.search(cr,uid,[('report_name','=',self._reports[report_id]['report_name'])])
            if report:
                report = report_obj.browse(cr,uid,report[0])
                name = report.name
                data = report.behaviour()[report.id]
                action = data['action']
                printer = data['printer']
                if action != 'client':
                    if (self._reports and self._reports.get(report_id, False) and self._reports[report_id].get('result', False)
                        and self._reports[report_id].get('format', False)):
                        report_obj.print_direct(cr, uid, report.id, base64.encodestring(self._reports[report_id]['result']),
                            self._reports[report_id]['format'], printer)
                        # XXX "Warning" removed as it breaks the workflow
                        # it would be interesting to have a dialog box to confirm if we really want to print
                        # in this case it must be with a by pass parameter to allow massive impression
                        #raise osv.except_osv(_('Printing...'), _('Document sent to printer %s') % (printer,))

        except:
            cr.rollback()
            raise
        finally:
            cr.close()

        res = super(virtual_report_spool, self).exp_report_get(db, uid, report_id)
        return res

virtual_report_spool()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
