# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Camptocamp SA
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
from openerp.osv.orm import browse_record
from .pingen import Pingen


class res_company(orm.Model):

    _inherit = 'res.company'

    _columns = {
        'pingen_token': fields.char('Pingen Token', size=32),
        'pingen_staging': fields.boolean('Pingen Staging')
    }

    def _pingen(self, cr, uid, company, context=None):
        """ Return a Pingen instance to work on """
        assert isinstance(company, (int, long, browse_record)), \
            "one id or browse_record expected"
        if not isinstance(company, browse_record):
            company = self.browse(cr, uid, company, context=context)
        return Pingen(company.pingen_token, staging=company.pingen_staging)
