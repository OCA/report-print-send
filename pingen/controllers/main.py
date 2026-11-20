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

    def _get_document_uuid(self, json_content):
        return (
            json_content.get("data", {})
            .get("relationships", {})
            .get("letter", {})
            .get("data", {})
            .get("id", "")
        )

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
        return json_content.get("data", {}).get("attributes", {}).get("reason", "")

    def _get_letter_infos(self, json_content, document_uuid):
        for node in json_content.get("included", {}):
            if node.get("type") == "letters" and node.get("id") == document_uuid:
                return node.get("attributes", {})
        return {}

    def _get_emitted_date(self, json_content):
        emitted_at = ""
        for node in json_content.get("included", {}):
            if node.get("type") == "letters_events":
                attributes = node.get("attributes", {})
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
