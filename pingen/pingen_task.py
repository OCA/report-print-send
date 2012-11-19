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


class pingen_task(orm.Model):
    """ A pingen task is the state of the synchronization of
    an attachment with pingen.com

    It stores the configuration and the current state of the synchronization.
    It also serves as a queue of documents to push to pingen.com
    """

    _name = 'pingen.task'
    _inherits = {'ir.attachment': 'attachment_id'}

    _columns = {
        'attachment_id': fields.many2one(
            'ir.attachment', 'Document', required=True, ondelete='cascade'),
        'state': fields.selection(
            [('pending', 'Pending'),
             ('pushed', 'Pushed'),
             ('error', 'Error'),
             ('canceled', 'Canceled')],
            string='State', readonly=True, required=True),
        'config': fields.text('Configuration (tmp)'),
    }

    _defaults = {
        'state': 'pending',
    }

    _sql_constraints = [
        ('pingen_task_attachment_uniq',
         'unique (attachment_id)',
         'Only one Pingen task is allowed per attachment.'),
    ]

