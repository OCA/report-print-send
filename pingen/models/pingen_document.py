# -*- coding: utf-8 -*-
# Author: Guewen Baconnier
# Copyright 2012-2017 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from itertools import groupby
from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from cStringIO import StringIO

import odoo
from odoo import models, fields, _
from odoo.exceptions import UserError
from .pingen import APIError, pingen_datetime_to_utc, POST_SENDING_STATUS


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
    auto_send = fields.Boolean(
        'Auto Send', help="Defines if a document is merely uploaded or also sent",
        default=True)
    delivery_product = fields.Selection(
        [
            ("fast","fast"),
            ("cheap","cheap"),
            ("bulk","bulk"),
            ("track","track"),
            ("sign","sign"),
            ("atpost_economy","atpost_economy"),
            ("atpost_priority","atpost_priority"),
            ("postag_a","postag_a"),
            ("postag_b","postag_b"),
            ("postag_b2","postag_b2"),
            ("postag_registered","postag_registered"),
            ("postag_aplus","postag_aplus"),
            ("dpag_standard","dpag_standard"),
            ("dpag_economy","dpag_economy"),
            ("indpost_mail","indpost_mail"),
            ("indpost_speedmail","indpost_speedmail"),
            ("nlpost_priority","nlpost_priority"),
            ("dhl_priority","dhl_priority"),
        ],
        "Delivery product",
        default="cheap",
    )
    print_spectrum = fields.Selection([("grayscale", "Grayscale"), ("color", "Color")], "Print Spectrum", default="grayscale")
    print_mode = fields.Selection([("simplex", "Simplex"), ("duplex", "Duplex")], "Print mode", default="simplex")

    push_date = fields.Datetime('Push Date', readonly=True)
    # for `error` and `pingen_error` states when we push
    last_error_message = fields.Text('Error Message', readonly=True)
    # pingen API v2 fields
    pingen_uuid = fields.Char(readonly=True)
    pingen_status = fields.Char()
    # sendcenter infos
    parsed_address = fields.Text('Parsed Address', readonly=True)
    cost = fields.Float('Cost', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    country_id = fields.Many2one('res.country', 'Country', readonly=True)
    send_date = fields.Datetime('Date of sending', readonly=True)
    pages = fields.Integer('Pages', readonly=True)
    company_id = fields.Many2one(related="attachment_id.company_id")

    # Deprecated fields
    pingen_id = fields.Integer(
        'Pingen ID', readonly=True,
        help="[DEPRECATED] ID of the document in the Pingen Documents (API v1)"
    )
    post_id = fields.Integer(
        'Pingen Post ID', readonly=True,
        help="[DEPRECATED] ID of the document in the Pingen Sendcenter (API v1)"
    )
    post_status = fields.Char('Post Status', size=128, readonly=True, help="[DEPRECATED] (API v1)")

    _sql_constraints = [
        ('pingen_document_attachment_uniq',
         'unique (attachment_id)',
         'Only one Pingen document is allowed per attachment.'),
    ]

    def _push_to_pingen(self, pingen=None):
        """ Push a document to pingen.com
        :param Pingen pingen: optional pingen object to reuse session
        """
        decoded_document = self.attachment_id._decoded_content()
        if pingen is None:
            pingen = self.company_id._get_pingen_client()
        try:
            doc_id, post_id, infos = pingen.push_document(
                self.name,
                StringIO(decoded_document),
                self.auto_send,
                self.delivery_product,
                self.print_spectrum,
                self.print_mode)
        except OAuth2Error as e:
            _logger.exception(
                'Connection Error when pushing Pingen Document with ID %s to %s: %s' %
                (self.id, pingen.api_url, e.description))
            raise
        except APIError:
            _logger.error(
                'API Error when pushing Pingen Document %s to %s.' %
                (self.id, pingen.api_url))
            raise
        error = False
        state = 'pushed'
        # if post_id:
        #     state = 'sendcenter'
        # elif infos['requirement_failure']:
        #     state = 'pingen_error'
        #     error = _('The document does not meet the Pingen requirements.')
        push_date = pingen_datetime_to_utc(infos.get('created_at'))
        self.write(
            {
                'last_error_message': error,
                'state': state,
                'push_date': fields.Datetime.to_string(push_date),
                'pingen_uuid': doc_id,
                'pingen_status': infos.get('status'),
            }
        )
        _logger.info(
            'Pingen Document %s: pushed to %s' % (self.id, pingen.api_url))

    def push_to_pingen(self):
        """ Push a document to pingen.com
        Convert errors to osv.except_osv to be handled by the client.
        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        self.ensure_one()
        state = False
        error_msg = False
        try:
            session = self.company_id._get_pingen_client()
            self._push_to_pingen(pingen=session)
        except OAuth2Error as e:
            state = 'error'
            error_msg = _('Connection Error when pushing document %s to Pingen') % self.name
        except APIError as e:
            state = 'pingen_error'
            error_msg = _('Error when pushing the document %s to Pingen:\n%s') % (self.name, e)
        except Exception as e:
            error_msg = _('Unexpected Error when pushing the document %s to Pingen:\n'%s) % (self.name, e)
            _logger.exception(error_msg)
        finally:
            if error_msg:
                vals = {'last_error_message': error_msg}
                if state:
                    vals.update({'state': state})
                with odoo.registry(self.env.cr.dbname).cursor() as new_cr:
                    new_env = odoo.api.Environment(
                        new_cr, self.env.uid, self.env.context)
                    self.with_env(new_env).write(vals)

                raise UserError(error_msg)
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
                not_sent_docs = self.search([('state', '!=', 'sent')], order="company_id")
                for company, documents in groupby(not_sent_docs, lambda d: d.company_id):
                    session = company._get_pingen_client()
                    for document in documents:
                        if document.state == 'error':
                            document._resolve_error()
                            document.refresh()
                        try:
                            if document.state == 'pending':
                                document._push_to_pingen(pingen=session)
                            elif document.state == 'pushed':
                                document._ask_pingen_send(pingen=session)
                        except OAuth2Error as e:
                            document.write({'last_error_message': e,
                                            'state': 'error'})
                        except APIError as e:
                            document.write({'last_error_message': e,
                                            'state': 'pingen_error'})
                        except BaseException as e:
                            _logger.error('Unexpected error in pingen cron')
        return True

    def _resolve_error(self):
        """ A document as resolved, put in the correct state """
        if self.post_id:
            state = 'sendcenter'
        elif self.pingen_uuid:
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
        try:
            infos = pingen.send_document(
                self.pingen_uuid,
                self.delivery_product,
                self.print_spectrum,
                self.print_mode
            )
        except OAuth2Error:
            _logger.exception(
                'Connection Error when asking for sending Pingen Document %s '
                'to %s.' % (self.id, pingen.api_url))
            raise
        except APIError:
            _logger.exception(
                'API Error when asking for sending Pingen Document %s to %s.' %
                (self.id, pingen.api_url))
            raise
        self.write(
            {
                'last_error_message': False,
                'state': 'sendcenter',
                'pingen_status': infos.get('status'),
            }
        )
        _logger.info(
            'Pingen Document %s: asked for sending to %s' % (
                self.id, pingen.api_url))
        return True

    def ask_pingen_send(self):
        """ For a document already pushed to pingen, ask to send it.
        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        self.ensure_one()
        try:
            session = self.company_id._get_pingen_client()
            self._ask_pingen_send(pingen=session)
        except OAuth2Error as e:
            raise UserError(
                _('Connection Error when asking for '
                  'sending the document %s to Pingen') % self.name)

        except APIError as e:
            raise UserError(
                _('Error when asking Pingen to send the document %s: '
                  '\n%s') % (self.name, e))

        except BaseException as e:
            _logger.exception(
                'Unexpected Error when updating the status '
                'of pingen.document %s: ' % self.id)
            raise UserError(
                _('Unexpected Error when updating the status '
                  'of Document %s') % self.name)
        return True

    def _update_post_infos(self, pingen):
        """ Update the informations from
        pingen of a document in the Sendcenter
        :param Pingen pingen: pingen object to reuse
        """
        if not self.pingen_uuid:
            return
        try:
            post_infos = pingen.post_infos(self.pingen_uuid)
        except OAuth2Error:
            _logger.exception(
                'Connection Error when asking for '
                'sending Pingen Document %s to %s.' %
                (self.id, pingen.api_url))
            raise
        except APIError:
            _logger.exception(
                'API Error when asking for sending Pingen Document %s to %s.' %
                (self.id, pingen.api_url))
            raise
        country = self.env['res.country'].search(
            [('code', '=', post_infos['country'])])
        currency = self.env["res.currency"].search(
            [("name", "=", post_infos.get("price_currency"))]
        )
        is_posted = pingen.is_posted(post_infos)
        if is_posted:
            post_date = post_infos.get("submitted_at")
            send_date = fields.Datetime.to_string(pingen_datetime_to_utc(post_date))
        else:
            send_date = False
        vals = {
            'pingen_status': post_infos.get('status'),
            'parsed_address': post_infos.get("address"),
            'country_id': country.id,
            'send_date': send_date,
            'pages': post_infos.get("file_pages"),
            'last_error_message': False,
            'cost': post_infos.get("price_value"),
            'currency_id': currency.id
        }
        if is_posted:
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
                    session = document.company_id._get_pingen_client()
                    try:
                        document._update_post_infos(pingen=session)
                    except (OAuth2Error, APIError):
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
        try:
            session = self.company_id._get_pingen_client()
            self._update_post_infos(pingen=session)
        except OAuth2Error as e:
            raise UserError(
                _('Connection Error when updating the status '
                  'of Document %s from Pingen') % self.name)
        except APIError as e:
            raise UserError(
                _('Error when updating the status of Document %s from '
                  'Pingen: \n%s') % (self.name, e))
        except BaseException as e:
            _logger.exception(
                'Unexpected Error when updating the status '
                'of pingen.document %s: ' % self.id)
            raise UserError(
                _('Unexpected Error when updating the status '
                  'of Document %s') % self.name)
        return True
