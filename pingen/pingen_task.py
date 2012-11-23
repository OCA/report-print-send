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

import logging
import datetime

from cStringIO import StringIO

from openerp.osv import orm, fields
from openerp import tools
from .pingen import Pingen, APIError, ConnectionError

# TODO should be configurable
TOKEN = '6bc041af6f02854461ef31c2121ef853'

_logger = logging.getLogger(__name__)


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
            'ir.attachment', 'Document', required=True, readonly=True, ondelete='cascade'),
        'state': fields.selection(
            [('pending', 'Pending'),
             ('pushed', 'Pushed'),
             ('sent', 'Sent'),
             ('error', 'Error'),
             ('need_fix', 'Needs a correction'),
             ('canceled', 'Canceled')],
            string='State', readonly=True, required=True),
        'date': fields.datetime('Creation Date'),
        'push_date': fields.datetime('Push Date'),
        'last_error_message': fields.text('Error Message', readonly=True),
        'pingen_id': fields.integer(
            'Pingen ID',
            help="ID of the document in the Pingen Documents"),
        'post_id': fields.integer(
            'Pingen Post ID',
            help="ID of the document in the Pingen Sendcenter"),
    }

    _defaults = {
        'state': 'pending',
    }

    _sql_constraints = [
        ('pingen_task_attachment_uniq',
         'unique (attachment_id)',
         'Only one Pingen task is allowed per attachment.'),
    ]

    def _push_to_pingen(self, cr, uid, task_id, context=None):
        """ Push a document to pingen.com


        """
        attachment_obj = self.pool.get('ir.attachment')
        task = self.browse(cr, uid, task_id, context=context)

        decoded_document = attachment_obj._decoded_content(
                cr, uid, task.attachment_id, context=context)

        success = False
        # parameterize
        pingen = Pingen(TOKEN, staging=True)
        doc = (task.datas_fname, StringIO(decoded_document))
        try:
            doc_id, post_id, __ = pingen.push_document(
                doc, task.pingen_send, task.pingen_speed, task.pingen_color)
        except ConnectionError as e:
            # we can continue and it will be retried the next time
            _logger.exception('Connection Error when pushing Pingen Task %s to %s.' %
                    (task.id, pingen.url))
            task.write(
                    {'last_error_message': e,
                     'state': 'error'},
                    context=context)

        except APIError as e:
            _logger.warning('API Error when pushing Pingen Task %s to %s.' %
                    (task.id, pingen.url))
            task.write(
                    {'last_error_message': e,
                     'state': 'need_fix'},
                    context=context)
        else:
            success = True

            now = datetime.datetime.now().strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
            task.write(
                {'last_error_message': False,
                 'state': 'pushed',
                 'push_date': now,
                 'pingen_id': doc_id,
                 'post_id': post_id},
                context=context)
            _logger.info('Pingen Task %s pushed to %s' % (task.id, pingen.url))

        return success

    def push_to_pingen(self, cr, uid, ids, context=None):
        """ Push a document to pingen.com

        Wrapper method for multiple ids (when triggered from button)
        """
        for task_id in ids:
            self._push_to_pingen(cr, uid, task_id, context=context)
        return True

