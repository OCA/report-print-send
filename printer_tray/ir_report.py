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
from openerp.osv import orm, fields


class ReportXML(orm.Model):

    _inherit = 'ir.actions.report.xml'

    _columns = {
        'printer_tray_id': fields.many2one(
            'printing.tray', 'Paper Source',
            domain="[('printer_id', '=', printing_printer_id)]"),
        }

    def set_print_options(self, cr, uid, report_id, format, context=None):
        """
        Hook to define Tray
        """
        printing_act_obj = self.pool.get('printing.report.xml.action')
        options = super(ReportXML, self).set_print_options(cr, uid, report_id, format, context=context)

        # Retrieve user default values
        user = self.pool.get('res.users').browse(cr, uid, context)
        tray = user.printer_tray_id
        report = self.browse(cr, uid, report_id, context=context)

        # Retrieve report default values
        if report.printer_tray_id:
            tray = report.printer_tray_id

        # Retrieve report-user specific values
        act_ids = printing_act_obj.search(
            cr, uid,
            [('report_id', '=', report.id),
             ('user_id', '=', uid),
             ('action', '!=', 'user_default')], context=context)
        if act_ids:
            user_action = printing_act_obj.browse(cr, uid, act_ids[0], context=context)
            if user_action.tray_id:
                tray = user_action.tray_id

        if tray:
            options['InputSlot'] = str(tray.system_name)
        return options
