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

from cStringIO import StringIO

from contextlib import closing
from openerp.osv import osv, orm, fields
from openerp.tools.translate import _
from openerp import pooler, tools
from .pingen import APIError, ConnectionError, POST_SENDING_STATUS, \
    pingen_datetime_to_utc

_logger = logging.getLogger(__name__)


class pingen_document(orm.Model):
    """ A pingen document is the state of the synchronization of
    an attachment with pingen.com

    It stores the configuration and the current state of the synchronization.
    It also serves as a queue of documents to push to pingen.com
    """

    _name = 'pingen.document'
    _inherits = {'ir.attachment': 'attachment_id'}

    _columns = {
        'attachment_id': fields.many2one(
            'ir.attachment', 'Document',
            required=True, readonly=True,
            ondelete='cascade'),
        'state': fields.selection(
            [('pending', 'Pending'),
             ('pushed', 'Pushed'),
             ('sendcenter', 'In Sendcenter'),
             ('sent', 'Sent'),
             ('error', 'Connection Error'),
             ('pingen_error', 'Pingen Error'),
             ('canceled', 'Canceled')],
            string='State', readonly=True, required=True),
        'push_date': fields.datetime('Push Date', readonly=True),

        # for `error` and `pingen_error` states when we push
        'last_error_message': fields.text('Error Message', readonly=True),

        # pingen IDs
        'pingen_id': fields.integer(
            'Pingen ID', readonly=True,
            help="ID of the document in the Pingen Documents"),
        'post_id': fields.integer(
            'Pingen Post ID', readonly=True,
            help="ID of the document in the Pingen Sendcenter"),

        # sendcenter infos
        'post_status': fields.char('Post Status', size=128, readonly=True),
        'parsed_address': fields.text('Parsed Address', readonly=True),
        'cost': fields.float('Cost', readonly=True),
        'currency_id': fields.many2one('res.currency', 'Currency', readonly=True),
        'country_id': fields.many2one('res.country', 'Country', readonly=True),
        'send_date': fields.datetime('Date of sending', readonly=True),
        'pages': fields.integer('Pages', readonly=True),
    }

    _defaults = {
        'state': 'pending',
    }

    _sql_constraints = [
        ('pingen_document_attachment_uniq',
         'unique (attachment_id)',
         'Only one Pingen document is allowed per attachment.'),
    ]

    def _get_pingen_session(self, cr, uid, context=None):
        """ Returns a pingen session for a user """
        company = self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id
        return self.pool.get('res.company')._pingen(cr, uid, company, context=context)

    def _push_to_pingen(self, cr, uid, document, pingen=None, context=None):
        """ Push a document to pingen.com

        :param Pingen pingen: optional pingen object to reuse session
        """
        attachment_obj = self.pool.get('ir.attachment')

        decoded_document = attachment_obj._decoded_content(
            cr, uid, document.attachment_id, context=context)

        if pingen is None:
            pingen = self._get_pingen_session(cr, uid, context=context)
        try:
            doc_id, post_id, infos = pingen.push_document(
                document.datas_fname,
                StringIO(decoded_document),
                document.pingen_send,
                document.pingen_speed,
                document.pingen_color)
        except ConnectionError:
            _logger.exception(
                'Connection Error when pushing Pingen Document %s to %s.' %
                (document.id, pingen.url))
            raise

        except APIError:
            _logger.error(
                'API Error when pushing Pingen Document %s to %s.' %
                (document.id, pingen.url))
            raise

        error = False
        state = 'pushed'
        if post_id:
            state = 'sendcenter'
        elif infos['requirement_failure']:
            state = 'pingen_error'
            error = _('The document does not meet the Pingen requirements.')

        push_date = pingen_datetime_to_utc(infos['date'])

        document.write(
            {'last_error_message': error,
             'state': state,
             'push_date': push_date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
             'pingen_id': doc_id,
             'post_id': post_id},
            context=context)
        _logger.info('Pingen Document %s: pushed to %s' % (document.id, pingen.url))

    def push_to_pingen(self, cr, uid, ids, context=None):
        """ Push a document to pingen.com

        Convert errors to osv.except_osv to be handled by the client.

        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        assert len(ids) == 1, "Only 1 id is allowed"
        with self._get_pingen_session(cr, uid, context=context) as session:
            for document in self.browse(cr, uid, ids, context=context):
                try:
                    self._push_to_pingen(
                        cr, uid, document, pingen=session, context=context)
                except ConnectionError as e:
                    raise osv.except_osv(
                        _('Pingen Connection Error'),
                        _('Connection Error when asking for sending the document %s to Pingen') % document.name)

                except APIError as e:
                    raise osv.except_osv(
                        _('Pingen Error'),
                        _('Error when asking Pingen to send the document %s: '
                          '\n%s') % (document.name, e))

                except:
                    _logger.exception(
                        'Unexcepted Error when updating the status of pingen.document %s: ' %
                        document.id)
                    raise osv.except_osv(
                        _('Error'),
                        _('Unexcepted Error when updating the status of Document %s') % document.name)
        return True

    def _push_and_send_to_pingen_cron(self, cr, uid, ids, context=None):
        """ Push a document to pingen.com

        Intended to be used in a cron.

        Commit after each record

        Instead of raising, store the error in the pingen.document
        """
        if not ids:
            ids = self.search(
                cr, uid,
                # do not retry pingen_error, they should be treated manually
                [('state', 'in', ['pending', 'pushed', 'error'])],
                limit=100,
                context=context)

        with closing(pooler.get_db(cr.dbname).cursor()) as loc_cr, \
                self._get_pingen_session(cr, uid, context=context) as session:
            for document in self.browse(loc_cr, uid, ids, context=context):

                if document.state == 'error':
                    self._resolve_error(loc_cr, uid, document, context=context)
                    document.refresh()

                try:
                    if document.state == 'pending':
                        self._push_to_pingen(
                            loc_cr, uid, document, pingen=session, context=context)

                    elif document.state == 'pushed':
                        self._ask_pingen_send(
                            loc_cr, uid, document, pingen=session, context=context)
                except ConnectionError as e:
                    document.write({'last_error_message': e,
                                    'state': 'error'},
                                   context=context)
                except APIError as e:
                    document.write({'last_error_message': e,
                                    'state': 'pingen_error'},
                                   context=context)
                except:
                    _logger.error('Unexcepted error in pingen cron')
                    loc_cr.rollback()
                    raise

                else:
                    loc_cr.commit()

        return True

    def _resolve_error(self, cr, uid, document, context=None):
        """ A document as resolved, put in the correct state """
        if document.post_id:
            state = 'sendcenter'
        elif document.pingen_id:
            state = 'pushed'
        else:
            state = 'pending'
        document.write({'state': state}, context=context)

    def resolve_error(self, cr, uid, ids, context=None):
        """ A document as resolved, put in the correct state """
        for document in self.browse(cr, uid, ids, context=context):
            self._resolve_error(cr, uid, document, context=context)
        return True

    def _ask_pingen_send(self, cr, uid, document, pingen, context=None):
        """ For a document already pushed to pingen, ask to send it.

        :param Pingen pingen: pingen object to reuse
        """
        # sending has been explicitely asked so we change the option
        # for consistency
        if not document.pingen_send:
            document.write({'pingen_send': True}, context=context)

        try:
            post_id = pingen.send_document(
                document.pingen_id,
                document.pingen_speed,
                document.pingen_color)
        except ConnectionError:
            _logger.exception('Connection Error when asking for sending Pingen Document %s to %s.' %
                              (document.id, pingen.url))
            raise
        except APIError:
            _logger.exception('API Error when asking for sending Pingen Document %s to %s.' %
                              (document.id, pingen.url))
            raise

        document.write(
            {'last_error_message': False,
             'state': 'sendcenter',
             'post_id': post_id},
            context=context)
        _logger.info('Pingen Document %s: asked for sending to %s' % (document.id, pingen.url))

        return True

    def ask_pingen_send(self, cr, uid, ids, context=None):
        """ For a document already pushed to pingen, ask to send it.

        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        assert len(ids) == 1, "Only 1 id is allowed"
        with self._get_pingen_session(cr, uid, context=context) as session:
            for document in self.browse(cr, uid, ids, context=context):
                try:
                    self._ask_pingen_send(cr, uid, document, pingen=session, context=context)
                except ConnectionError as e:
                    raise osv.except_osv(
                        _('Pingen Connection Error'),
                        _('Connection Error when asking for '
                          'sending the document %s to Pingen') % document.name)

                except APIError as e:
                    raise osv.except_osv(
                        _('Pingen Error'),
                        _('Error when asking Pingen to send the document %s: '
                          '\n%s') % (document.name, e))

                except:
                    _logger.exception(
                        'Unexcepted Error when updating the status of pingen.document %s: ' %
                        document.id)
                    raise osv.except_osv(
                        _('Error'),
                        _('Unexcepted Error when updating the status of Document %s') % document.name)
        return True

    def _update_post_infos(self, cr, uid, document, pingen, context=None):
        """ Update the informations from pingen of a document in the Sendcenter

        :param Pingen pingen: pingen object to reuse
        """
        if not document.post_id:
            return

        try:
            post_infos = pingen.post_infos(document.post_id)
        except ConnectionError:
            _logger.exception(
                'Connection Error when asking for '
                'sending Pingen Document %s to %s.' %
                (document.id, pingen.url))
            raise
        except APIError:
            _logger.exception(
                'API Error when asking for sending Pingen Document %s to %s.' %
                (document.id, pingen.url))
            raise

        currency_ids = self.pool.get('res.currency').search(
            cr, uid, [('name', '=', post_infos['currency'])], context=context)
        country_ids = self.pool.get('res.country').search(
            cr, uid, [('code', '=', post_infos['country'])], context=context)

        send_date = pingen_datetime_to_utc(post_infos['date'])

        vals = {
            'post_status': POST_SENDING_STATUS[post_infos['status']],
            'cost': post_infos['cost'],
            'currency_id': currency_ids[0] if currency_ids else False,
            'parsed_address': post_infos['address'],
            'country_id': country_ids[0] if country_ids else False,
            'send_date': send_date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
            'pages': post_infos['pages'],
            'last_error_message': False,
            }
        if pingen.is_posted(post_infos):
            vals['state'] = 'sent'

        document.write(vals, context=context)
        _logger.info('Pingen Document %s: status updated' % document.id)

    def _update_post_infos_cron(self, cr, uid, ids, context=None):
        """ Update the informations from pingen of a document in the Sendcenter

        Intended to be used in a cron.

        Commit after each record

        Do not raise errors, only skip the update of the record.
        """
        if not ids:
            ids = self.search(
                cr, uid,
                [('state', '=', 'sendcenter')],
                context=context)

        with closing(pooler.get_db(cr.dbname).cursor()) as loc_cr, \
                self._get_pingen_session(cr, uid, context=context) as session:
            for document in self.browse(loc_cr, uid, ids, context=context):
                try:
                    self._update_post_infos(
                        loc_cr, uid, document, pingen=session, context=context)
                except (ConnectionError, APIError):
                    # will be retried the next time
                    # In any case, the error has been logged by _update_post_infos
                    loc_cr.rollback()
                except:
                    _logger.error('Unexcepted error in pingen cron')
                    loc_cr.rollback()
                    raise
                else:
                    loc_cr.commit()
        return True

    def update_post_infos(self, cr, uid, ids, context=None):
        """ Update the informations from pingen of a document in the Sendcenter

        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        assert len(ids) == 1, "Only 1 id is allowed"
        with self._get_pingen_session(cr, uid, context=context) as session:
            for document in self.browse(cr, uid, ids, context=context):
                try:
                    self._update_post_infos(
                        cr, uid, document, pingen=session, context=context)
                except ConnectionError as e:
                    raise osv.except_osv(
                        _('Pingen Connection Error'),
                        _('Connection Error when updating the status of Document %s'
                          ' from Pingen') % document.name)

                except APIError as e:
                    raise osv.except_osv(
                        _('Pingen Error'),
                        _('Error when updating the status of Document %s from Pingen: '
                          '\n%s') % (document.name, e))

                except:
                    _logger.exception(
                        'Unexcepted Error when updating the status of pingen.document %s: ' %
                        document.id)
                    raise osv.except_osv(
                        _('Error'),
                        _('Unexcepted Error when updating the status of Document %s') % document.name)
        return True
