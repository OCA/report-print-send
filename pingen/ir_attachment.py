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

from openerp.osv import osv, orm, fields
from openerp.tools.translate import _


class ir_attachment(orm.Model):

    _inherit = 'ir.attachment'

    _columns = {
        'send_to_pingen': fields.boolean('Send to Pingen.com'),
        'pingen_task_ids': fields.one2many(
            'pingen.task', 'attachment_id',
            string="Pingen Task", readonly=True),
    }

    def _prepare_pingen_task_vals(self, cr, uid, attachment, context=None):
        return {'attachment_id': attachment.id,
                'config': 'created from attachment'}

    def _handle_pingen_task(self, cr, uid, attachment_id, context=None):
        """ Reponsible of the related ``pingen.task`` when the ``send_to_pingen``
        field is modified.

        Only one pingen task can be created per attachment.

        When ``send_to_pingen`` is activated:
          * Create a ``pingen.task`` if it does not already exist
          * Put the related ``pingen.task`` to ``pending`` if it already exist
        When it is deactivated:
          * Do nothing if no related ``pingen.task`` exists
          * Or cancel it
          * If it has already been pushed to pingen.com, raises
            an `osv.except_osv` exception
        """
        pingen_task_obj = self.pool.get('pingen.task')
        attachment = self.browse(cr, uid, attachment_id, context=context)
        task = attachment.pingen_task_ids[0] if attachment.pingen_task_ids else None
        if attachment.send_to_pingen:
            if task:
                task.write({'state': 'pending'}, context=context)
            else:
                pingen_task_obj.create(
                        cr, uid,
                        self._prepare_pingen_task_vals(
                            cr, uid, attachment, context=context),
                        context=context)
        else:
            if task:
                if task.state == 'pushed':
                    raise osv.except_osv(
                        _('Error'),
                        _('The attachment %s is already pushed to pingen.com.') % \
                            attachment.name)
                task.write({'state': 'canceled'}, context=context)
        return

    def create(self, cr, uid, vals, context=None):
        attachment_id = super(ir_attachment, self).create(cr, uid, vals, context=context)
        if 'send_to_pingen' in vals:
            self._handle_pingen_task(cr, uid, attachment_id, context=context)
        return attachment_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(ir_attachment, self).write(cr, uid, ids, vals, context=context)
        if 'send_to_pingen' in vals:
            for attachment_id in ids:
                self._handle_pingen_task(cr, uid, attachment_id, context=context)
        return res

