# Copyright 2022 Camptocamp SA
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
    def _verify_signature(self, request_content):
        webhook_signature = http.request.httprequest.headers.get("Signature")
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
            if webhook_signature == secret_signature:
                return company
        msg = "Webhook signature does not match with any company secret"
        _logger.warning(msg)
        raise werkzeug.exceptions.Forbidden()

    def _get_request_content(self):
        return http.request.httprequest.stream.read()

    def _get_json_content(self, request_content):
        return json.loads(request_content)

    def _get_document_uuid(self, json_content):
        return (
            json_content.get("data", {})
            .get("relationships", {})
            .get("letter", {})
            .get("data", {})
            .get("id", "")
        )

    def _find_pingen_document(self, document_uuid):
        if document_uuid:
            return http.request.env["pingen.document"].search(
                [("pingen_uuid", "=", document_uuid)]
            )
        return http.request.env["pingen.document"].browse()

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
        return pingen_datetime_to_utc(emitted_at.encode())

    def _update_pingen_document(self, request_content, values):
        json_content = self._get_json_content(request_content)
        document_uuid = self._get_document_uuid(json_content)
        pingen_doc = self._find_pingen_document(document_uuid)
        if pingen_doc:
            info_values = pingen_doc._prepare_values_from_post_infos(
                self._get_letter_infos(json_content, document_uuid)
            )
            info_values.update(values)
            pingen_doc.sudo().write(info_values)
            msg = "Pingen document with UUID %s updated successfully" % document_uuid
            _logger.info(msg)
            return msg
        msg = "Could not find related Pingen document for UUID %s" % document_uuid
        _logger.warning(msg)
        return msg

    @http.route(
        "/pingen/letter_issues", type="http", auth="none", methods=["POST"], csrf=False
    )
    def letter_issues(self, **post):
        _logger.info("Webhook call received on /pingen/letter_issues")
        request_content = self._get_request_content()
        json_content = self._get_json_content(request_content)
        self._verify_signature(request_content)
        values = {
            "state": "pingen_error",
            "last_error_message": self._get_error_reason(json_content),
        }
        self._update_pingen_document(request_content, values)

    @http.route(
        "/pingen/sent_letters", type="http", auth="none", methods=["POST"], csrf=False
    )
    def sent_letters(self, **post):
        _logger.info("Webhook call received on /pingen/sent_letters")
        request_content = self._get_request_content()
        json_content = self._get_json_content(request_content)
        self._verify_signature(request_content)
        emitted_date = self._get_emitted_date(json_content)
        values = {
            "state": "sent",
        }
        if emitted_date:
            values["send_date"] = emitted_date
        self._update_pingen_document(request_content, values)

    @http.route(
        "/pingen/undeliverable_letters",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def undeliverable_letters(self, **post):
        _logger.info("Webhook call received on /pingen/undeliverable_letters")
        request_content = self._get_request_content()
        json_content = self._get_json_content(request_content)
        self._verify_signature(request_content)
        values = {
            "state": "error_undeliverable",
            "last_error_message": self._get_error_reason(json_content),
        }
        self._update_pingen_document(request_content, values)
