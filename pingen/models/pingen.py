# -*- coding: utf-8 -*-
# Author: Guewen Baconnier
# Copyright 2012-2017 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import requests
import logging
import urlparse
import json
import pytz

from datetime import datetime
from requests.packages.urllib3.filepost import encode_multipart_formdata

_logger = logging.getLogger(__name__)

POST_SENDING_STATUS = {
    100: 'Ready/Pending',
    101: 'Processing',
    102: 'Waiting for confirmation',
    1: 'Sent',
    300: 'Some error occured and object wasn\'t sent',
    400: 'Sending cancelled',
}

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'  # this is the format used by pingen API

TZ = pytz.timezone('Europe/Zurich')  # this is the timezone of the pingen API


def pingen_datetime_to_utc(dt):
    """ Convert a date/time used by pingen.com to UTC timezone

    :param dt: pingen date/time as string (as received from the API)
               to convert to UTC
    :return: datetime in the UTC timezone
    """
    utc = pytz.utc
    dt = datetime.strptime(dt, DATETIME_FORMAT)
    localized_dt = TZ.localize(dt, is_dst=True)
    return localized_dt.astimezone(utc)


class PingenException(RuntimeError):
    """There was an ambiguous exception that occurred while handling your
    request."""


class APIError(PingenException):
    """An Error occured with the pingen API"""


class Pingen(object):
    """ Interface to the pingen.com API """

    def __init__(self, token, staging=True):
        self._token = token
        self.staging = staging
        self._session = None
        super(Pingen, self).__init__()

    @property
    def url(self):
        if self.staging:
            return 'https://stage-api.pingen.com'
        return 'https://api.pingen.com'

    @property
    def session(self):
        """ Build a requests session """
        if self._session is not None:
            return self._session
        self._session = requests.Session()
        self._session.params = {'token': self._token}
        self._session.verify = not self.staging
        return self._session

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        """Dispose of any internal state. """
        if self._session:
            self._session.close()

    def _send(self, method, endpoint, **kwargs):
        """ Send a request to the pingen API using requests

        Add necessary boilerplate to call pingen.com API
        (authentication, configuration, ...)

        :param boundmethod method: requests method to call
        :param str endpoint: endpoint to call
        :param kwargs: additional arguments forwarded to the requests method
        """

        p_url = urlparse.urljoin(self.url, endpoint)

        if endpoint == 'document/get':
            complete_url = '{}{}{}{}{}'.format(p_url,
                                               '/id/',
                                               kwargs['params']['id'],
                                               '/token/',
                                               self._token)
        else:
            complete_url = '{}{}{}'.format(p_url,
                                           '/token/',
                                           self._token)

        response = method(complete_url, **kwargs)

        if response.json()['error']:
            raise APIError(
                "%s: %s" % (response.json()['errorcode'],
                            response.json()['errormessage']))

        return response

    def push_document(self, filename, filestream,
                      send=None, speed=None, color=None):
        """ Upload a document to pingen.com and eventually ask to send it

        :param str filename: name of the file to push
        :param StringIO filestream: file to push
        :param boolean send: if True, the document will be sent by pingen.com
        :param int/str speed: sending speed of the document if it is send
                                1 = Priority, 2 = Economy
        :param int/str color: type of print, 0 = B/W, 1 = Color
        :return: tuple with 3 items:
                 1. document_id on pingen.com
                 2. post_id on pingen.com if it has been sent or None
                 3. dict of the created item on pingen (details)
        """
        data = {
            'send': send,
            'speed': speed,
            'color': color,
            }

        # we cannot use the `files` param alongside
        # with the `datas`param when data is a
        # JSON-encoded data. We have to construct
        # the entire body and send it to `data`
        # https://github.com/kennethreitz/requests/issues/950
        formdata = {
            'file': (filename, filestream.read()),
            'data': json.dumps(data),
            }

        multipart, content_type = encode_multipart_formdata(formdata)

        response = self._send(
            self.session.post,
            'document/upload',
            headers={'Content-Type': content_type},
            data=multipart)

        rjson = response.json()

        document_id = rjson['id']
        if rjson.get('send'):
            # confusing name but send_id is the posted id
            posted_id = rjson['send'][0]['send_id']
        item = rjson['item']

        return document_id, posted_id, item

    def send_document(self, document_id, speed=None, color=None):
        """ Send a uploaded document to pingen.com

        :param int document_id: id of the document to send
        :param int/str speed: sending speed of the document if it is send
                                1 = Priority, 2 = Economy
        :param int/str color: type of print, 0 = B/W, 1 = Color
        :return: id of the post on pingen.com
        """
        data = {
            'speed': speed,
            'color': color,
            }
        response = self._send(
            self.session.post,
            'document/send',
            params={'id': document_id},
            data={'data': json.dumps(data)})

        return response.json()['id']

    def post_infos(self, post_id):
        """ Return the information of a post

        :param int post_id: id of the document to send
        :return: dict of infos of the post
        """
        response = self._send(
            self.session.get,
            'document/get',
            params={'id': post_id})

        return response.json()['item']

    @staticmethod
    def is_posted(post_infos):
        """ return True if the post has been sent

        :param dict post_infos: post infos returned by `post_infos`
        """
        return post_infos['status'] == 1
