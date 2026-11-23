# Copyright 2022 Camptocamp SA
# Copyright 2026 Altixia LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import hashlib
import hmac
import json
import logging

import werkzeug

from odoo import http

from ..models.pingen import pingen_datetime_to_utc

_logger = logging.getLogger(__name__)

# ``data.type`` of the webhooks this module receives (Pingen OpenAPI schemas).
WEBHOOK_TYPES = frozenset(
    ("webhook_issues", "webhook_sent", "webhook_undeliverable", "webhook_delivered")
)


def _as_dict(value):
    """``value`` if it is a JSON object, else an empty one."""
    return value if isinstance(value, dict) else {}


class PingenController(http.Controller):
    # The webhooks write on pingen.document. Since 18.0 an ``auth="none"``
    # route runs in a read-only transaction by default (then retries in
    # read/write after a failed UPDATE), hence ``readonly=False`` below.

    def _verify_signature(self, request_content):
        """Return the company whose webhook secret signed ``request_content``.

        The comparison is constant-time: a plain ``==`` leaks, through its
        timing, how many leading characters of a forged signature are right.
        """
        webhook_signature = http.request.httprequest.headers.get("Signature") or ""
        companies = http.request.env["res.company"].sudo().search([])
        for company in companies:
            # We could not search on `pingen_webhook_secret
            # if this field is computed (e.g. env field)
            if not company.pingen_webhook_secret:
                continue
            secret_signature = hmac.new(
                company.pingen_webhook_secret.encode("utf-8"),
                request_content,
                hashlib.sha256,
            ).hexdigest()
            if hmac.compare_digest(webhook_signature, secret_signature):
                return company
        _logger.warning("Webhook signature does not match with any company secret")
        raise werkzeug.exceptions.Forbidden()

    def _get_request_content(self):
        return http.request.httprequest.get_data()

    def _get_json_content(self, request_content):
        try:
            return json.loads(request_content)
        except ValueError as e:
            raise werkzeug.exceptions.BadRequest() from e

    def _get_relationship_data(self, json_content, name):
        data = _as_dict(_as_dict(json_content).get("data"))
        relationships = _as_dict(data.get("relationships"))
        return _as_dict(_as_dict(relationships.get(name)).get("data"))

    def _get_deliverable_type(self, json_content):
        """Type of the deliverable named by the webhook (letters, emails...)."""
        return self._get_relationship_data(json_content, "deliverable").get("type")

    def _get_document_uuid(self, json_content):
        # Pingen names the letter ``deliverable`` (``letter`` in older payloads).
        deliverable = self._get_relationship_data(json_content, "deliverable")
        if deliverable:
            if deliverable.get("type", "letters") != "letters":
                return ""
            if deliverable.get("id"):
                return deliverable["id"]
        return self._get_relationship_data(json_content, "letter").get("id") or ""

    def _find_pingen_document(self, document_uuid, company=None):
        # The route is public (auth="none"): search as superuser, but only
        # among the documents of the company that signed the call.
        documents = http.request.env["pingen.document"].sudo()
        if not document_uuid:
            return documents.browse()
        domain = [("pingen_uuid", "=", document_uuid)]
        if company:
            domain.append(("company_id", "=", company.id))
        return documents.search(domain, limit=1)

    def _get_error_reason(self, json_content):
        data = _as_dict(_as_dict(json_content).get("data"))
        return _as_dict(data.get("attributes")).get("reason") or ""

    def _get_included(self, json_content):
        included = _as_dict(json_content).get("included")
        if not isinstance(included, list):
            return []
        return [node for node in included if isinstance(node, dict)]

    def _get_letter_infos(self, json_content, document_uuid):
        for node in self._get_included(json_content):
            if node.get("type") == "letters" and node.get("id") == document_uuid:
                return _as_dict(node.get("attributes"))
        return {}

    def _get_emitted_date(self, json_content):
        emitted_at = ""
        for node in self._get_included(json_content):
            if node.get("type") in ("deliverables_events", "letters_events"):
                attributes = _as_dict(node.get("attributes"))
                if attributes.get("code") == "transferred_to_distributor":
                    emitted_at = attributes.get("emitted_at", "")
                    break
        return pingen_datetime_to_utc(emitted_at)

    def _update_pingen_document(self, request_content, values, company=None):
        json_content = self._get_json_content(request_content)
        document_uuid = self._get_document_uuid(json_content)
        pingen_doc = self._find_pingen_document(document_uuid, company=company)
        if pingen_doc:
            info_values = pingen_doc._prepare_values_from_post_infos(
                self._get_letter_infos(json_content, document_uuid)
            )
            info_values.update(values)
            pingen_doc.write(info_values)
            msg = f"Pingen document with UUID {document_uuid} updated successfully"
            _logger.info(msg)
            return msg
        msg = f"Could not find related Pingen document for UUID {document_uuid}"
        _logger.warning(msg)
        return msg

    def _receive(self, route, values_getter):
        """Common webhook flow: authenticate first, then parse and apply."""
        _logger.info("Webhook call received on %s", route)
        request_content = self._get_request_content()
        company = self._verify_signature(request_content)
        json_content = self._get_json_content(request_content)
        document_uuid = self._get_document_uuid(json_content)
        if not document_uuid:
            deliverable_type = self._get_deliverable_type(json_content)
            if deliverable_type and deliverable_type != "letters":
                msg = "Webhook deliverable is not a letter, ignored"
                _logger.info("%s on %s", msg, route)
                return msg
            # A 4xx makes Pingen retry the call and show it as failed, instead
            # of a silent success when its payload format changes.
            # Only a known webhook type reaches the log, never payload data.
            webhook_type = _as_dict(_as_dict(json_content).get("data")).get("type")
            if not isinstance(webhook_type, str) or webhook_type not in WEBHOOK_TYPES:
                webhook_type = "unexpected"
            _logger.error(
                "Webhook on %s names no letter (data.type %s)", route, webhook_type
            )
            raise werkzeug.exceptions.BadRequest()
        values = values_getter(json_content)
        return self._update_pingen_document(request_content, values, company=company)

    @http.route(
        "/pingen/letter_issues",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
        readonly=False,
    )
    def letter_issues(self, **post):
        return self._receive(
            "/pingen/letter_issues",
            lambda json_content: {
                "state": "pingen_error",
                "last_error_message": self._get_error_reason(json_content),
            },
        )

    def _sent_values(self, json_content):
        values = {"state": "sent"}
        emitted_date = self._get_emitted_date(json_content)
        if emitted_date:
            values["send_date"] = emitted_date
        return values

    @http.route(
        "/pingen/sent_letters",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
        readonly=False,
    )
    def sent_letters(self, **post):
        return self._receive("/pingen/sent_letters", self._sent_values)

    @http.route(
        "/pingen/delivered_letters",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
        readonly=False,
    )
    def delivered_letters(self, **post):
        return self._receive("/pingen/delivered_letters", self._sent_values)

    @http.route(
        "/pingen/undeliverable_letters",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
        readonly=False,
    )
    def undeliverable_letters(self, **post):
        return self._receive(
            "/pingen/undeliverable_letters",
            lambda json_content: {
                "state": "error_undeliverable",
                "last_error_message": self._get_error_reason(json_content),
            },
        )
