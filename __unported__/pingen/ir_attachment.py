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

import requests
import base64

from openerp.osv import osv, orm, fields
from openerp.tools.translate import _


class ir_attachment(orm.Model):

    _inherit = 'ir.attachment'

    _columns = {
        'send_to_pingen': fields.boolean('Send to Pingen.com'),
        'pingen_document_ids': fields.one2many(
            'pingen.document', 'attachment_id',
            string='Pingen Document', readonly=True),
        'pingen_send': fields.boolean(
            'Send',
            help="Defines if a document is merely uploaded or also sent"),
        'pingen_speed': fields.selection(
            [('1', 'Priority'), ('2', 'Economy')],
            'Speed',
            help="Defines the sending speed if the document is automatically sent"),
        'pingen_color': fields.selection([('0', 'B/W'), ('1', 'Color')], 'Type of print'),
    }

    _defaults = {
        'pingen_send': True,
        'pingen_color': '0',
        'pingen_speed': '2',
    }

    def _prepare_pingen_document_vals(self, cr, uid, attachment, context=None):
        return {'attachment_id': attachment.id,
                'config': 'created from attachment'}

    def _handle_pingen_document(self, cr, uid, attachment_id, context=None):
        """ Reponsible of the related ``pingen.document`` when the ``send_to_pingen``
        field is modified.

        Only one pingen document can be created per attachment.

        When ``send_to_pingen`` is activated:
          * Create a ``pingen.document`` if it does not already exist
          * Put the related ``pingen.document`` to ``pending`` if it already exist
        When it is deactivated:
          * Do nothing if no related ``pingen.document`` exists
          * Or cancel it
          * If it has already been pushed to pingen.com, raises
            an `osv.except_osv` exception
        """
        pingen_document_obj = self.pool.get('pingen.document')
        attachment = self.browse(cr, uid, attachment_id, context=context)
        document = attachment.pingen_document_ids[0] if attachment.pingen_document_ids else None
        if attachment.send_to_pingen:
            if document:
                document.write({'state': 'pending'}, context=context)
            else:
                pingen_document_obj.create(
                    cr, uid,
                    self._prepare_pingen_document_vals(
                        cr, uid, attachment, context=context),
                    context=context)
        else:
            if document:
                if document.state == 'pushed':
                    raise osv.except_osv(
                        _('Error'),
                        _('The attachment %s is already pushed to pingen.com.') %
                        attachment.name)
                document.write({'state': 'canceled'}, context=context)
        return

    def create(self, cr, uid, vals, context=None):
        attachment_id = super(ir_attachment, self).create(cr, uid, vals, context=context)
        if 'send_to_pingen' in vals:
            self._handle_pingen_document(cr, uid, attachment_id, context=context)
        return attachment_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(ir_attachment, self).write(cr, uid, ids, vals, context=context)
        if 'send_to_pingen' in vals:
            for attachment_id in ids:
                self._handle_pingen_document(cr, uid, attachment_id, context=context)
        return res

    def _decoded_content(self, cr, uid, attachment, context=None):
        """ Returns the decoded content of an attachment (stored or url)

        Returns None if the type is 'url' and the url is not reachable.
        """
        decoded_document = None
        if attachment.type == 'binary':
            decoded_document = base64.decodestring(attachment.datas)
        elif attachment.type == 'url':
            response = requests.get(attachment.url)
            if response.ok:
                decoded_document = requests.content
        else:
            raise Exception(
                'The type of attachment %s is not handled' % attachment.type)
        return decoded_document
