# Author: Guewen Baconnier
# Copyright 2012-2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import datetime
from urllib.parse import urljoin

import pytz
import requests
from dateutil import parser
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

_logger = logging.getLogger(__name__)


def pingen_datetime_to_utc(dt):
    """Convert a date/time used by pingen.com to UTC timezone

    :param dt: pingen date/time iso string (as received from the API)
               to convert to UTC
    :return: TZ naive datetime in the UTC timezone
    """
    utc = pytz.utc
    localized_dt = parser.parse(dt)
    return localized_dt.astimezone(utc).replace(tzinfo=None)


class PingenException(RuntimeError):
    """There was an ambiguous exception that occurred while handling your
    request."""


class APIError(PingenException):
    """An Error occured with the pingen API"""


class Pingen(object):
    """Interface to the pingen.com API"""

    def __init__(self, clientid, secretid, organization, staging=True):
        self.clientid = clientid
        self.secretid = secretid
        self.organization = organization
        self.staging = staging
        self._session = None
        self._init_token_registry()
        super(Pingen, self).__init__()

    @property
    def api_url(self):
        if self.staging:
            return "https://api-staging.pingen.com"
        return "https://api.pingen.com"

    @property
    def identity_url(self):
        if self.staging:
            return "https://identity-staging.pingen.com"
        return "https://identity.pingen.com"

    @property
    def token_url(self):
        return "auth/access-tokens"

    @property
    def file_upload_url(self):
        return "file-upload"

    @property
    def session(self):
        """Build a requests session"""
        if self._session is not None:
            return self._session
        client = BackendApplicationClient(client_id=self.clientid)
        self._session = OAuth2Session(client=client)
        self._set_session_header_token()
        return self._session

    @classmethod
    def _init_token_registry(cls):
        if hasattr(cls, "token_registry"):
            return
        cls.token_registry = {
            "staging": {"token": "", "expiry": datetime.now()},
            "prod": {"token": "", "expiry": datetime.now()},
        }

    @classmethod
    def _get_token_infos(cls, staging):
        if staging:
            return cls.token_registry.get("staging")
        else:
            return cls.token_registry.get("prod")

    @classmethod
    def _set_token_data(cls, token_data, staging):
        token_string = " ".join(
            [token_data.get("token_type"), token_data.get("access_token")]
        )
        token_expiry = datetime.fromtimestamp(token_data.get("expires_at"))
        if staging:
            cls.token_registry["staging"] = {
                "token": token_string,
                "expiry": token_expiry,
            }
        else:
            cls.token_registry["prod"] = {"token": token_string, "expiry": token_expiry}

    def _fetch_token(self):
        # TODO: Handle scope 'letter' only?
        token_url = urljoin(self.identity_url, self.token_url)
        # FIXME: requests.exceptions.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
        # certificate verify failed (_ssl.c:581)
        #  without verify=False parameter on prod/staging
        _logger.debug("Fetching new token from %s" % token_url)
        return self._session.fetch_token(
            token_url=token_url,
            client_id=self.clientid,
            client_secret=self.secretid,
            verify=False,
        )

    def _set_session_header_token(self):
        if self._is_token_expired():
            token_data = self._fetch_token()
            self._set_token_data(token_data, self.staging)
        token_infos = self._get_token_infos(self.staging)
        self._session.headers["Authorization"] = token_infos.get("token")

    def _is_token_expired(self):
        token_infos = self._get_token_infos(self.staging)
        expired = token_infos.get("expiry") <= datetime.now()
        if expired:
            _logger.debug("Pingen token is expired")
        return expired

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        """Dispose of any internal state."""
        if self._session:
            self._session.close()

    def _send(self, method, endpoint, letter_id="", **kwargs):
        """Send a request to the pingen API using requests

        Add necessary boilerplate to call pingen.com API
        (authentication, configuration, ...)

        :param boundmethod method: requests method to call
        :param str endpoint: endpoint to call
        :param kwargs: additional arguments forwarded to the requests method
        """

        if self._is_token_expired():
            self._set_session_header_token()

        p_url = urljoin(self.api_url, endpoint)

        if endpoint == "document/get":
            complete_url = "{}{}{}{}{}".format(
                p_url, "/id/", kwargs["params"]["id"], "/token/", self._token
            )
        else:
            complete_url = p_url.format(
                organisationId=self.organization, letterId=letter_id
            )
        response = method(complete_url, verify=False, **kwargs)
        errors = response.json().get("errors")
        if errors:
            raise APIError(
                "\n".join(
                    [
                        "%s (%s): %s"
                        % (err.get("code"), err.get("title"), err.get("detail"))
                        for err in errors
                    ]
                )
            )
        return response

    def _get_file_upload(self):
        _logger.debug("Getting new URL for file upload")
        response = self._send(self.session.get, self.file_upload_url)
        json_response_attributes = response.json().get("data", {}).get("attributes")
        url = json_response_attributes.get("url")
        url_signature = json_response_attributes.get("url_signature")
        return url, url_signature

    def upload_file(self, url, multipart, content_type):
        _logger.debug("Uploading new file")
        response = requests.put(
            url, data=multipart, headers={"Content-Type": content_type}, timeout=30
        )
        return response

    def push_document(
        self,
        filename,
        filestream,
        content_type,
        send=None,
        delivery_product=None,
        print_spectrum=None,
        print_mode=None,
    ):
        """Upload a document to pingen.com and eventually ask to send it

        :param str filename: name of the file to push
        :param StringIO filestream: file to push
        :param boolean send: if True, the document will be sent by pingen.com
        :param str delivery_product: sending product of the document if it is send
        :param str print_spectrum: type of print, grayscale or color
        :return: tuple with 3 items:
                 1. document_id on pingen.com
                 2. post_id on pingen.com if it has been sent or None
                 3. dict of the created item on pingen (details)
        """

        url, url_signature = self._get_file_upload()
        self.upload_file(url, filestream.read(), content_type)

        data_attributes = {
            "file_original_name": filename,
            "file_url": url,
            "file_url_signature": url_signature,
            "address_position": "left",
            "auto_send": send,
            "delivery_product": delivery_product,
            "print_spectrum": print_spectrum,
            "print_mode": print_mode,
        }

        data = {"data": {"type": "letters", "attributes": data_attributes}}

        response = self._send(
            self.session.post,
            "organisations/{organisationId}/letters",
            headers={"Content-Type": "application/vnd.api+json"},
            data=json.dumps(data),
        )
        rjson_data = response.json().get("data", {})

        document_id = rjson_data.get("id")
        item = rjson_data.get("attributes")

        return document_id, False, item

    def send_document(
        self, document_uuid, delivery_product=None, print_spectrum=None, print_mode=None
    ):
        """Send a uploaded document to pingen.com

        :param str document_uuid: id of the document to send
        :param str delivery_product: sending product of the document
        :param str print_spectrum: type of print, grayscale or color
        :return: id of the post on pingen.com
        """
        data_attributes = {
            "delivery_product": delivery_product,
            "print_mode": print_mode,
            "print_spectrum": print_spectrum,
        }
        data = {
            "data": {
                "id": document_uuid,
                "type": "letters",
                "attributes": data_attributes,
            }
        }
        response = self._send(
            self.session.patch,
            "organisations/{organisationId}/letters/{letterId}/send",
            letter_id=document_uuid,
            headers={"Content-Type": "application/vnd.api+json"},
            data=json.dumps(data),
        )
        return response.json().get("data", {}).get("attributes")

    def post_infos(self, document_uuid):
        """Return the information of a post

        :param str document_uuid: id of the document to send
        :return: dict of infos of the post
        """
        response = self._send(
            self.session.get,
            "organisations/{organisationId}/letters/{letterId}",
            letter_id=document_uuid,
        )
        return response.json().get("data", {}).get("attributes")
