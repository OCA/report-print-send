# -*- coding: utf-8 -*-
# Author: Guewen Baconnier
# Copyright 2012-2017 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from cStringIO import StringIO

# from contextlib import closing
from odoo import models, fields, _
from odoo.exceptions import UserError
import odoo
from .pingen import APIError, ConnectionError, \
    POST_SENDING_STATUS, pingen_datetime_to_utc

_logger = logging.getLogger(__name__)


class PingenDocument(models.Model):
    """ A pingen document is the state of the synchronization of
    an attachment with pingen.com

    It stores the configuration and the current state of the synchronization.
    It also serves as a queue of documents to push to pingen.com
    """

    _name = 'pingen.document'
    _inherits = {'ir.attachment': 'attachment_id'}

    attachment_id = fields.Many2one(
        'ir.attachment', 'Document',
        required=True, readonly=True,
        ondelete='cascade')
    state = fields.Selection(
        [('pending', 'Pending'),
         ('pushed', 'Pushed'),
         ('sendcenter', 'In Sendcenter'),
         ('sent', 'Sent'),
         ('error', 'Connection Error'),
         ('pingen_error', 'Pingen Error'),
         ('canceled', 'Canceled')],
        string='State', readonly=True,
        required=True, default='pending')
    push_date = fields.Datetime('Push Date', readonly=True)
    # for `error` and `pingen_error` states when we push
    last_error_message = fields.Text('Error Message', readonly=True)
    # pingen IDs
    pingen_id = fields.Integer(
        'Pingen ID', readonly=True,
        help="ID of the document in the Pingen Documents")
    post_id = fields.Integer(
        'Pingen Post ID', readonly=True,
        help="ID of the document in the Pingen Sendcenter")
    # sendcenter infos
    post_status = fields.Char('Post Status', size=128, readonly=True)
    parsed_address = fields.Text('Parsed Address', readonly=True)
    cost = fields.Float('Cost', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    country_id = fields.Many2one('res.country', 'Country', readonly=True)
    send_date = fields.Datetime('Date of sending', readonly=True)
    pages = fields.Integer('Pages', readonly=True)

    _sql_constraints = [
        ('pingen_document_attachment_uniq',
         'unique (attachment_id)',
         'Only one Pingen document is allowed per attachment.'),
    ]

    def _get_pingen_session(self):
        """ Returns a pingen session for a user """
        return self.company_id._pingen()

    def _push_to_pingen(self, pingen=None):
        """ Push a document to pingen.com
        :param Pingen pingen: optional pingen object to reuse session
        """
        decoded_document = self.attachment_id._decoded_content()
        if pingen is None:
            pingen = self._get_pingen_session()
        try:
            doc_id, post_id, infos = pingen.push_document(
                self.datas_fname,
                StringIO(decoded_document),
                self.pingen_send,
                self.pingen_speed,
                self.pingen_color)
        except ConnectionError:
            _logger.exception(
                'Connection Error when pushing Pingen Document %s to %s.' %
                (self.id, pingen.url))
            raise
        except APIError:
            _logger.error(
                'API Error when pushing Pingen Document %s to %s.' %
                (self.id, pingen.url))
            raise
        error = False
        state = 'pushed'
        if post_id:
            state = 'sendcenter'
        elif infos['requirement_failure']:
            state = 'pingen_error'
            error = _('The document does not meet the Pingen requirements.')
        push_date = pingen_datetime_to_utc(infos['date'])
        self.write(
            {'last_error_message': error,
             'state': state,
             'push_date': fields.Datetime.to_string(push_date),
             'pingen_id': doc_id,
             'post_id': post_id},)
        _logger.info(
            'Pingen Document %s: pushed to %s' % (self.id, pingen.url))

    def push_to_pingen(self):
        """ Push a document to pingen.com
        Convert errors to osv.except_osv to be handled by the client.
        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        self.ensure_one()
        for document in self:
            try:
                session = self._get_pingen_session()
                document._push_to_pingen(pingen=session)
            except ConnectionError as e:
                raise UserError(
                    _('Connection Error when asking for ' +
                      'sending the document %s to Pingen')
                    % document.name)
            except APIError as e:
                raise UserError(
                    _('Error when asking Pingen to send the document %s: '
                      '\n%s') % (document.name, e))
            except Exception as e:
                _logger.exception(
                    'Unexcepted Error when updating ' +
                    'the status of pingen.document %s: ' %
                    document.id)
                raise UserError(
                    _('Unexcepted Error when updating the ' +
                      'status of Document %s') % document.name)
        return True

    def _push_and_send_to_pingen_cron(self):
        """ Push a document to pingen.com
        Intended to be used in a cron.
        Commit after each record
        Instead of raising, store the error in the pingen.document
        """
        with odoo.api.Environment.manage():
            with odoo.registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = odoo.api.Environment(
                    new_cr, self.env.uid, self.env.context)
                # Instead of raising, store the error in the pingen.document
                self = self.with_env(new_env)
                not_sent_docs = self.search([('state', '!=', 'sent')])
                for document in not_sent_docs:
                    session = document._get_pingen_session()
                    if document.state == 'error':
                        document._resolve_error()
                        document.refresh()
                    try:
                        if document.state == 'pending':
                            document._push_to_pingen(pingen=session)
                        elif document.state == 'pushed':
                            document._ask_pingen_send(pingen=session)
                    except ConnectionError as e:
                        document.write({'last_error_message': e,
                                        'state': 'error'})
                    except APIError as e:
                        document.write({'last_error_message': e,
                                        'state': 'pingen_error'})
                    except BaseException as e:
                        _logger.error('Unexcepted error in pingen cron')
        return True

    def _resolve_error(self):
        """ A document as resolved, put in the correct state """
        if self.post_id:
            state = 'sendcenter'
        elif self.pingen_id:
            state = 'pushed'
        else:
            state = 'pending'
        self.write({'state': state})

    def resolve_error(self):
        """ A document as resolved, put in the correct state """
        for document in self:
            document._resolve_error()
        return True

    def _ask_pingen_send(self, pingen):
        """ For a document already pushed to pingen, ask to send it.
        :param Pingen pingen: pingen object to reuse
        """
        # sending has been explicitely asked so we change the option
        # for consistency

        if not self.pingen_send:
            self.write({'pingen_send': True})
        try:
            post_id = pingen.send_document(
                self.pingen_id,
                self.pingen_speed,
                self.pingen_color)
        except ConnectionError:
            _logger.exception(
                'Connection Error when asking for sending ' +
                'Pingen Document %s to %s.' %
                (self.id, pingen.url))
            raise
        except APIError:
            _logger.exception(
                'API Error when asking for sending ' +
                'Pingen Document %s to %s.' %
                (self.id, pingen.url))
            raise
        self.write(
            {'last_error_message': False,
             'state': 'sendcenter',
             'post_id': post_id})
        _logger.info(
            'Pingen Document %s: asked for' +
            'sending to %s' % (self.id, pingen.url))
        return True

    def ask_pingen_send(self):
        """ For a document already pushed to pingen, ask to send it.
        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        self.ensure_one()
        for document in self:
            try:
                session = document._get_pingen_session()
                document._ask_pingen_send(pingen=session)
            except ConnectionError as e:
                raise UserError(
                    _('Connection Error when asking for '
                      'sending the document %s to Pingen') % document.name)

            except APIError as e:
                raise UserError(
                    _('Error when asking Pingen to send the document %s: '
                      '\n%s') % (document.name, e))

            except BaseException as e:
                _logger.exception(
                    'Unexcepted Error when updating the ' +
                    'status of pingen.document %s: ' %
                    document.id)
                raise UserError(
                    _('Unexcepted Error when updating the ' +
                      'status of Document %s') % document.name)
        return True

    def _update_post_infos(self, pingen):
        """ Update the informations from
        pingen of a document in the Sendcenter
        :param Pingen pingen: pingen object to reuse
        """
        if not self.pingen_id:
            return
        try:
            post_infos = pingen.post_infos(self.pingen_id)
        except ConnectionError:
            _logger.exception(
                'Connection Error when asking for '
                'sending Pingen Document %s to %s.' %
                (self.id, pingen.url))
            raise
        except APIError:
            _logger.exception(
                'API Error when asking for sending ' +
                'Pingen Document %s to %s.' %
                (self.id, pingen.url))
            raise
        # currency_ids = self.env['res.currency'].search(
        #     [('name', '=', post_infos['currency'])])
        country = self.env['res.country'].search(
            [('code', '=', post_infos['country'])])
        send_date = pingen_datetime_to_utc(post_infos['date'])
        vals = {
            # 'post_status': POST_SENDING_STATUS[post_infos['status']],
            # 'cost': post_infos['cost'],
            # 'currency_id': currency_ids[0] if currency_ids else False,
            'parsed_address': post_infos['address'],
            'country_id': country.id if country else False,
            'send_date': fields.Datetime.to_string(send_date),
            # 'pages': post_infos['pages'],
            'last_error_message': False,
            }
        if pingen.is_posted(post_infos):
            vals['state'] = 'sent'
        self.write(vals)
        _logger.info('Pingen Document %s: status updated' % self.id)

    def _update_post_infos_cron(self):
        """ Update the informations from pingen of a
        document in the Sendcenter
        Intended to be used in a cron.
        Commit after each record
        Do not raise errors, only skip the update of the record."""
        with odoo.api.Environment.manage():
            with odoo.registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = odoo.api.Environment(
                    new_cr, self.env.uid, self.env.context)
                # Instead of raising, store the error in the pingen.document
                self = self.with_env(new_env)
                pushed_docs = self.search([('state', '!=', 'sent')])
                for document in pushed_docs:
                    session = document._get_pingen_session()
                    try:
                        document._update_post_infos(pingen=session)
                    except (ConnectionError, APIError):
                        # will be retried the next time
                        # In any case, the error has been
                        # logged by _update_post_infos
                        pass
                    except BaseException as e:
                        _logger.error('Unexcepted error in pingen cron: %', e)
                        raise
        return True

    def update_post_infos(self):
        """ Update the informations from pingen of a document in the Sendcenter
        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        self.ensure_one()
        for document in self:
            try:
                session = document._get_pingen_session()
                document._update_post_infos(pingen=session)
            except ConnectionError as e:
                raise UserError(
                    _('Connection Error when updating ' +
                      'the status of Document %s'
                      ' from Pingen') % document.name)
            except APIError as e:
                raise UserError(
                    _('Error when updating the status ' +
                      'of Document %s from Pingen: '
                      '\n%s') % (document.name, e))
            except BaseException as e:
                _logger.exception(
                    'Unexcepted Error when updating ' +
                    'the status of pingen.document %s: ' %
                    document.id)
                raise UserError(
                    _('Unexcepted Error when updating ' +
                      'the status of Document %s') % document.name)
        return True
