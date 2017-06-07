# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
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

from openerp.osv import osv

import logging
_logger = logging.getLogger(__name__)

class email_template(osv.osv):
    _inherit = "email.template"
    
    def generate_email_batch(self, cr, uid, template_id, res_ids, context={}, fields=None):
        ctx = context.copy()
        ctx['must_skip_send_to_printer'] = True
        return super(email_template, self).generate_email_batch(cr, uid, template_id, res_ids, context=ctx, fields=fields)
