# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
#    Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
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
from openerp import models, fields, api

from .printing import _available_action_types


class ReportXmlAction(models.Model):
    _name = 'printing.report.xml.action'
    _description = 'Report Printing Actions'

    report_id = fields.Many2one(comodel_name='ir.actions.report.xml',
                                string='Report',
                                required=True,
                                ondelete='cascade')
    user_id = fields.Many2one(comodel_name='res.users',
                              string='User',
                              required=True,
                              ondelete='cascade')
    action = fields.Selection(_available_action_types,
                              required=True)
    printer_id = fields.Many2one(comodel_name='printing.printer',
                                 string='Printer')

    @api.multi
    def behaviour(self):
        if not self:
            return {}
        return {'action': self.action,
                'printer': self.printer_id,
                }
