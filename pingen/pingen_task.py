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
import urlparse
import base64
import logging

from cStringIO import StringIO

from openerp.osv import orm, fields

# TODO should be configurable
BASE_URL = 'https://stage-api.pingen.com'
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
            'ir.attachment', 'Document', required=True, ondelete='cascade'),
        'state': fields.selection(
            [('pending', 'Pending'),
             ('pushed', 'Pushed'),
             ('error', 'Error'),
             ('canceled', 'Canceled')],
            string='State', readonly=True, required=True),
        'config': fields.text('Configuration (tmp)'),
        'date': fields.datetime('Creation Date'),
        'push_date': fields.datetime('Pushed Date'),
        'send': fields.boolean(
            'Send',
            help="Defines if a document is merely uploaed or also sent"),
        'speed': fields.selection(
            [(1, 'Priority'), (2, 'Economy')],
            'Speed',
            help="Defines the sending speed if the document is automatically sent"),
        'color': fields.selection( [(0, 'B/W'), (1, 'Color')], 'Type of print'),
        'last_error_code': fields.integer('Error Code', readonly=True),
        'last_error_message': fields.text('Error Message', readonly=True),
        'pingen_id': fields.integer('Pingen ID'),

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
        success = False
        push_url = urlparse.urljoin(BASE_URL, 'document/upload')
        auth = {'token': TOKEN}

        config = {
            'send': False,
            'speed': 2,
            'color': 1,
            }

        task = self.browse(cr, uid, task_id, context=context)

        if task.type == 'binary':
            decoded_document = base64.decodestring(task.datas)
        else:
            url_resp = requests.get(task.url)
            if url_resp.status_code != 200:
                task.write({'last_error_code': False,
                            'last_error_message': "%s" % req.error,
                            'state': 'error'},
                           context=context)
                return False
            decoded_document = requests.content

        document = {'file': (task.datas_fname, StringIO(decoded_document))}
        try:
            # TODO extract
            req = requests.post(
                    push_url,
                    params=auth,
                    data=config,
                    files=document,
                    # verify = False required for staging environment
                    verify=False)
            req.raise_for_status()
        except (requests.HTTPError,
                requests.Timeout,
                requests.ConnectionError) as e:
            msg = ('%s Message: %s. \n'
                    'It occured when pushing the Pingen Task %s to pingen.com. \n'
                    'It will be retried later.' % (e.__doc__, e, task.id))
            _logger.error(msg)
            task.write(
                    {'last_error_code': False,
                     'last_error_message': msg,
                     'state': 'error'},
                    context=context)
        else:
            response = req.json
            if response['error']:
                task.write(
                        {'last_error_code': response['errorcode'],
                         'last_error_message': 'Error from pingen.com: %s' % response['errormessage'],
                         'state': 'error'},
                        context=context)
            else:
                task.write(
                    {'last_error_code': False,
                     'last_error_message': False,
                     'state': 'pushed',
                     'pingen_id': response['id'],},
                    context=context)
                _logger.info('Pingen Task %s pushed to pingen.com.' % task.id)
                success = True

        return success

    def push_to_pingen(self, cr, uid, ids, context=None):
        """ Push a document to pingen.com

        Wrapper method for multiple ids (when triggered from button)
        """
        for task_id in ids:
            self._push_to_pingen(cr, uid, task_id, context=context)
        return True


        # r = requests.get(push_url, params=auth, verify=False)


        # TODO: resolve = put in pending or put in pushed


