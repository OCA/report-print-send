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
import logging
import urlparse

_logger = logging.getLogger(__name__)


class PingenException(RuntimeError):
    """There was an ambiguous exception that occurred while handling your
    request."""


class ConnectionError(PingenException):
    """An Error occured with the pingen API"""


class APIError(PingenException):
    """An Error occured with the pingen API"""



class Pingen(object):
    """ Interface to pingen.com API
    """

    def __init__(self, token, staging=True):
        self._token = token
        self.staging = True
        super(Pingen, self).__init__()

    @property
    def url(self):
        if self.staging:
            return 'https://stage-api.pingen.com'
        return 'https://api.pingen.com'

    def _send(self, method, endpoint, **kwargs):
        """ Send a request to the pingen API using requests

        Add necessary boilerplate to call pingen.com API
        (authentication, configuration, ...)

        :param boundmethod method: requests method to call
        :param str endpoint: endpoint to call
        :param kwargs: additional arguments forwarded to the requests method
        """
        complete_url = urlparse.urljoin(self.url, endpoint)

        auth_param = {'token': self._token}
        if 'params' in kwargs:
            kwargs['params'].update(auth_param)
        else:
            kwargs['params'] = auth_param

        # with safe_mode, requests catch errors and
        # returns a blank response with an error
        config = {'safe_mode': True}
        if 'config' in kwargs:
            kwargs['config'].update(config)
        else:
            kwargs['config'] = config

        # verify = False required for staging environment
        # because the SSL certificate is wrong
        kwargs['verify'] = not self.staging
        response = method(complete_url, **kwargs)

        if not response.ok:
            raise ConnectionError(response.error)

        if response.json['error']:
            raise APIError(
                    "%s: %s" % (response.json['errorcode'], response.json['errormessage']))

        return response

    def push_document(self, document, send=None, speed=None, color=None):
        """ Upload a document to pingen.com and eventually ask to send it

        :param tuple document: (filename, file stream) to push
        :param boolean send: if True, the document will be sent by pingen.com
        :param int/str speed: sending speed of the document if it is send
                                1 = Priority, 2 = Economy
        :param int/str color: type of print, 0 = B/W, 1 = Color
        :return: tuple with 3 items:
                 1. document_id on pingen.com
                 2. post_id on pingen.com if it has been sent or None
                 3. dict of the created item on pingen (details)
        """
        document = {'file': document}
        data = {
            'send': send,
            'speed': speed,
            'color': color,
            }
        response = self._send(
                requests.post,
                'document/upload',
                data=data,
                files=document)

        json = response.json

        document_id = json['id']
        # confusing name but send_id is the posted id
        posted_id = json.get('send', {}).get('send_id')
        item = json['item']

        return document_id, posted_id, item

    def send_document(self, document_id, speed=None, color=None):
        """ Send a uploaded document to pingen.com

        :param int document_id: id of the document to send
        :param int/str speed: sending speed of the document if it is send
                                1 = Priority, 2 = Economy
        :param int/str color: type of print, 0 = B/W, 1 = Color
        :return: id of the post on pingen.com
        """
        response = self._send(
                requests.post,
                'document/send',
                params={'id': document_id})

        return response.json['id']

