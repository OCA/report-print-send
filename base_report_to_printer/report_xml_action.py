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
from openerp.osv import orm, fields

from printing import _available_action_types

class report_xml_action(orm.Model):
    _name = 'printing.report.xml.action'
    _description = 'Report Printing Actions'
    _columns = {
        'report_id': fields.many2one('ir.actions.report.xml', 'Report', required=True, ondelete='cascade'),
        'user_id': fields.many2one('res.users', 'User', required=True, ondelete='cascade'),
        'action': fields.selection(_available_action_types, 'Action', required=True),
        'printer_id': fields.many2one('printing.printer', 'Printer'),
        }


    def behaviour(self, cr, uid, act_id, context=None):
        result = {}
        if not act_id:
            return False
        action = self.browse(cr, uid, act_id, context=context)
        return {
            'action': action.action,
            'printer': action.printer_id,
            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
