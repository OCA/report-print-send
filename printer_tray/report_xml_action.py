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


class ReportXMLAction(orm.Model):
    _inherit = 'printing.report.xml.action'

    _columns = {
        'printer_tray_id': fields.many2one(
            'printing.tray', 'Paper Source',
            domain="[('printer_id', '=', printer_id)]"),
        }

    def behaviour(self, cr, uid, act_id, context=None):
        res = super(ReportXMLAction, self).behaviour(cr, uid, act_id, context=context)
        action = self.browse(cr, uid, act_id, context=context)
        res['tray'] = action.printer_tray_id.system_name
        return res
