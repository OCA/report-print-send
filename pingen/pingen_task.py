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

from openerp.osv import osv, orm, fields
from openerp import tools
from openerp.tools.translate import _
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
             ('sendcenter', 'In Sendcenter'),
             ('sent', 'Sent'),
             ('error', 'Connection Error'),
             ('pingen_error', 'Pingen Error'),
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

    def _push_to_pingen(self, cr, uid, task, context=None):
        """ Push a document to pingen.com """
        attachment_obj = self.pool.get('ir.attachment')

        decoded_document = attachment_obj._decoded_content(
                cr, uid, task.attachment_id, context=context)

        pingen = self._pingen(cr, uid, [], context=context)
        try:
            doc_id, post_id, __ = pingen.push_document(
                task.datas_fname,
                StringIO(decoded_document),
                task.pingen_send,
                task.pingen_speed,
                task.pingen_color)
        except ConnectionError as e:
            _logger.exception('Connection Error when pushing Pingen Task %s to %s.' %
                    (task.id, pingen.url))
            raise

        except APIError as e:
            _logger.error('API Error when pushing Pingen Task %s to %s.' %
                    (task.id, pingen.url))
            raise

        now = datetime.datetime.now().strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
        task.write(
            {'last_error_message': False,
             'state': 'sendcenter' if post_id else 'pushed',
             'push_date': now,
             'pingen_id': doc_id,
             'post_id': post_id},
            context=context)
        _logger.info('Pingen Task %s pushed to %s' % (task.id, pingen.url))

    def push_to_pingen(self, cr, uid, ids, context=None):
        """ Push a document to pingen.com

        Convert errors to osv.except_osv to be handled by the client.

        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        for task in self.browse(cr, uid, ids, context=context):
            try:
                self._push_to_pingen(cr, uid, task, context=context)
            except ConnectionError as e:
                raise osv.except_osv(
                    _('Pingen Connection Error'),
                    _('Connection Error when asking for sending the document %s to Pingen') % task.name)

            except APIError as e:
                raise osv.except_osv(
                    _('Pingen Error'),
                    _('Error when asking Pingen to send the document %s: '
                      '\n%s') % (task.name, e))
        return True

    def _push_to_pingen_with_logs(self, cr, uid, ids, context=None):
        """ Push a document to pingen.com

        Instead of raising, store the error in the pingen.document
        """
        for task in self.browse(cr, uid, ids, context=context):
            try:
                self._push_to_pingen(cr, uid, task, context=context)
            except ConnectionError as e:
                task.write({'last_error_message': e, 'state': 'error'}, context=context)
            except APIError as e:
                task.write({'last_error_message': e, 'state': 'pingen_error'}, context=context)
        return True

    def _pingen(self, cr, uid, ids, context=None):
        """
        """
        assert not ids, "ids is there by convention, should not be used"
        # TODO parameterize
        return Pingen(TOKEN, staging=True)

    def _ask_pingen_send(self, cr, uid, task, context=None):
        """ For a document already pushed to pingen, ask to send it.
        """
        # sending has been explicitely asked so we change the option
        # for consistency
        if not task.pingen_send:
            task.write({'pingen_send': True}, context=context)

        pingen = self._pingen(cr, uid, [], context=context)
        try:
            post_id = pingen.send_document(
                task.pingen_id,
                task.pingen_speed,
                task.pingen_color)
        except ConnectionError as e:
            _logger.exception('Connection Error when asking for sending Pingen Task %s to %s.' %
                    (task.id, pingen.url))
            raise
        except APIError as e:
            _logger.exception('API Error when asking for sending Pingen Task %s to %s.' %
                    (task.id, pingen.url))
            raise

        task.write(
            {'last_error_message': False,
             'state': 'sendcenter',
             'post_id': post_id},
            context=context)
        _logger.info('Pingen Task %s asked for sending to %s' % (task.id, pingen.url))

        return True

    def ask_pingen_send(self, cr, uid, ids, context=None):
        """ For a document already pushed to pingen, ask to send it.

        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        for task in self.browse(cr, uid, ids, context=context):
            try:
                self._ask_pingen_send(cr, uid, task, context=context)
            except ConnectionError as e:
                raise osv.except_osv(
                    _('Pingen Connection Error'),
                    _('Connection Error when asking for sending the document %s to Pingen') % task.name)

            except APIError as e:
                raise osv.except_osv(
                    _('Pingen Error'),
                    _('Error when asking Pingen to send the document %s: '
                      '\n%s') % (task.name, e))
        return True

