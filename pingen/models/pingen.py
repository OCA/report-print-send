# Author: Guewen Baconnier
# Copyright 2012-2023 Camptocamp SA
# Copyright 2026 Altixia LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
import math
import uuid
from datetime import datetime, timedelta
from urllib.parse import urljoin

import pytz
import requests
from dateutil import parser
from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from requests_oauthlib import OAuth2Session

_logger = logging.getLogger(__name__)

# Seconds before a request to pingen.com is abandoned. requests has no default
# timeout: without one a stalled endpoint blocks the worker (and the cron)
# forever.
REQUEST_TIMEOUT = 30
UPLOAD_TIMEOUT = 120
# Re-fetch the token this long before it expires.
TOKEN_EXPIRY_MARGIN = timedelta(seconds=60)


def pingen_datetime_to_utc(dt):
    """Convert a date/time used by pingen.com to UTC timezone

    :param dt: pingen date/time iso string (as received from the API)
               to convert to UTC
    :return: TZ naive datetime in the UTC timezone, or None when ``dt`` is empty
    """
    if not dt:
        return None
    utc = pytz.utc
    localized_dt = parser.parse(dt)
    return localized_dt.astimezone(utc).replace(tzinfo=None)


class PingenException(RuntimeError):
    """There was an ambiguous exception that occurred while handling your
    request."""


class APIError(PingenException):
    """An Error occured with the pingen API"""


class NotFoundError(APIError):
    """The requested entity no longer exists on Pingen."""


class Pingen:
    """Interface to the pingen.com API (v2)

    Letters live under ``/organisations/{organisationId}/deliveries/letters``
    since Pingen's March 2026 API reorganisation (the official SDKs moved to
    these endpoints in their 2.21 releases).
    """

    # Access tokens cached per (environment, client id): two companies with
    # their own Pingen accounts must never share a token.
    token_registry = {}

    def __init__(
        self,
        clientid,
        secretid,
        organization,
        staging=True,
        verify=True,
        address_position="left",
    ):
        self.clientid = clientid
        self.secretid = secretid
        self.organization = organization
        self.staging = staging
        self.verify = verify
        self.address_position = address_position or "left"
        self._session = None
        super().__init__()

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
    def letters_url(self):
        return "organisations/{organisationId}/deliveries/letters"

    @property
    def _token_key(self):
        return ("staging" if self.staging else "prod", self.clientid)

    @property
    def session(self):
        """Build a requests session"""
        if self._session is not None:
            return self._session
        # Only the ``letter`` scope is needed: the organisation id is configured.
        client = BackendApplicationClient(client_id=self.clientid, scope=["letter"])
        self._session = OAuth2Session(client=client, scope=["letter"])
        self._set_session_header_token()
        return self._session

    def _fetch_token(self):
        token_url = urljoin(self.identity_url, self.token_url)
        _logger.debug("Fetching new token from %s", token_url)
        return self._session.fetch_token(
            token_url=token_url,
            client_id=self.clientid,
            client_secret=self.secretid,
            verify=self.verify,
            timeout=REQUEST_TIMEOUT,
        )

    def _set_token_data(self, token_data):
        token_string = " ".join(
            [token_data.get("token_type"), token_data.get("access_token")]
        )
        token_expiry = datetime.fromtimestamp(token_data.get("expires_at"))
        self.token_registry[self._token_key] = {
            "token": token_string,
            "expiry": token_expiry,
        }

    def _set_session_header_token(self):
        if self._is_token_expired():
            token_data = self._fetch_token()
            self._set_token_data(token_data)
        token_infos = self.token_registry[self._token_key]
        self._session.headers["Authorization"] = token_infos.get("token")

    def _is_token_expired(self):
        token_infos = self.token_registry.get(self._token_key)
        expired = (
            not token_infos
            or token_infos.get("expiry") - TOKEN_EXPIRY_MARGIN <= datetime.now()
        )
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
        complete_url = p_url.format(
            organisationId=self.organization, letterId=letter_id
        )
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        response = method(complete_url, verify=self.verify, **kwargs)
        try:
            payload = response.json() if response.content else {}
        except ValueError:
            payload = {}
        errors = payload.get("errors") if isinstance(payload, dict) else None
        not_found = response.status_code == 404 or any(
            err.get("code") == "entity_not_found" for err in (errors or [])
        )
        error_class = NotFoundError if not_found else APIError
        if errors:
            raise error_class(
                "\n".join(
                    [
                        f"{err.get('code')} ({err.get('title')}): {err.get('detail')}"
                        for err in errors
                    ]
                )
            )
        if not_found or not response.ok:
            raise error_class(f"HTTP {response.status_code} on {endpoint}")
        return response

    def organisation_reachable(self):
        """Check the organisation before treating missing letters as deleted."""
        try:
            self._send(self.session.get, "organisations/{organisationId}")
        except (APIError, OAuth2Error):
            return False
        return True

    @staticmethod
    def _json_api_headers():
        """JSON:API headers for a mutating call.

        The Idempotency-Key lets pingen.com replay its first answer (for 24 h)
        instead of acting twice when a request is retried after a timeout.
        """
        return {
            "Content-Type": "application/vnd.api+json",
            "Idempotency-Key": str(uuid.uuid4()),
        }

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
            url,
            data=multipart,
            headers={"Content-Type": content_type},
            timeout=UPLOAD_TIMEOUT,
        )
        if not response.ok:
            raise APIError(f"File upload failed: HTTP {response.status_code}")
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
            "address_position": self.address_position,
            "auto_send": bool(send),
            "delivery_product": delivery_product,
            "print_spectrum": print_spectrum,
            "print_mode": print_mode,
        }

        data = {"data": {"type": "letters", "attributes": data_attributes}}

        response = self._send(
            self.session.post,
            self.letters_url,
            headers=self._json_api_headers(),
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
            self.letters_url + "/{letterId}/send",
            letter_id=document_uuid,
            headers=self._json_api_headers(),
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
            self.letters_url + "/{letterId}",
            letter_id=document_uuid,
        )
        return response.json().get("data", {}).get("attributes")

    def price_quote(
        self, country, delivery_product, print_mode, print_spectrum, paper_types
    ):
        """Return a non-binding price and currency for the selected options."""
        data = {
            "data": {
                "type": "letter_price_calculator",
                "attributes": {
                    "country": country,
                    "delivery_product": delivery_product,
                    "print_mode": print_mode,
                    "print_spectrum": print_spectrum,
                    "paper_types": paper_types,
                },
            }
        }
        response = self._send(
            self.session.post,
            self.letters_url + "/price-calculator",
            headers=self._json_api_headers(),
            data=json.dumps(data),
        )
        attributes = response.json().get("data", {}).get("attributes") or {}
        price = attributes.get("price")
        if (
            isinstance(price, (int, float))
            and not isinstance(price, bool)
            and math.isfinite(price)
            and price > 0
        ):
            return price, attributes.get("currency")
        return None, None
