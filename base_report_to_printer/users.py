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

#
# Users
#
class res_users(orm.Model):
    _name = "res.users"
    _inherit = "res.users"

    def _user_available_action_types(self, cr, uid, context=None):
        if context is None:
            context={}
        return [x for x in _available_action_types(self, cr, uid, context) if x[0] != 'user_default']

    _columns = {
        'printing_action': fields.selection(_user_available_action_types, 'Printing Action'),
        'printing_printer_id': fields.many2one('printing.printer', 'Default Printer'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
