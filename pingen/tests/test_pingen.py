# Copyright 2012-2023 Camptocamp SA
# Copyright 2026 Altixia LLC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from os.path import dirname, join
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import pymupdf
from freezegun import freeze_time
from vcr import VCR

from odoo.exceptions import UserError
from odoo.tests import HttpCase, tagged
from odoo.tests.common import _super_send

from ..models.pingen import Pingen

vcr_pingen = VCR(
    record_mode="once",
    cassette_library_dir=join(dirname(__file__), "fixtures/cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    match_on=("method", "uri"),
    decode_compressed_response=True,
)

logging.basicConfig()
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.INFO)

ORGANISATION = "4c08c24e-65f8-47cf-b280-518ee76e3437"
WEBHOOK_SECRET = "pingen-test-webhook-secret"


@tagged("post_install", "-at_install")
class TestPingen(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.user.company_id
        cls.company.write(
            {
                "pingen_clientid": "1234",
                "pingen_client_secretid": "1234567893",
                "pingen_organization": ORGANISATION,
                "pingen_staging": True,
                "pingen_webhook_secret": WEBHOOK_SECRET,
            }
        )

    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        # Odoo blocks external HTTP in tests before VCR (which patches below
        # requests) can answer: let the Pingen hosts through to the cassette.
        # In record_mode "once" VCR refuses any request it has not recorded.
        host = urlparse(r.url).hostname or ""
        if host.endswith(".pingen.com") or host.endswith(".cloudscale.ch"):
            return _super_send(s, r, **kw)
        return super()._request_handler(s, r, **kw)

    def setUp(self):
        super().setUp()
        # Tokens are cached on the class: never leak one between tests.
        Pingen.token_registry.clear()
        self.addCleanup(Pingen.token_registry.clear)

    # flake8: noqa: B950
    def get_request_json(self, uuid, events=None):
        return json.dumps(
            {
                "data": {
                    "type": "webhook_issues",
                    "id": "735582d1-ccdf-423a-b493-1b3a6935df29",
                    "attributes": {
                        "reason": "Validation failed",
                        "url": r"https:\/\/example.com\/\/pingen\/letter_issues",
                        "created_at": "2023-05-19T09:35:01+0200",
                    },
                    "relationships": {
                        "organisation": {
                            "data": {"type": "organisations", "id": ORGANISATION},
                        },
                        "letter": {
                            "data": {"type": "letters", "id": uuid},
                        },
                        "event": {
                            "data": {
                                "type": "letters_events",
                                "id": "a9612d08-81c0-4259-8b0a-648c85377f71",
                            }
                        },
                    },
                },
                "included": [
                    {
                        "type": "letters",
                        "id": uuid,
                        "attributes": {
                            "status": "action_required",
                            "file_original_name": "in_invoice_yourcompany_demo.pdf",
                            "file_pages": 1,
                            "address": "405 Pushp Business Campus\nAhmedabad\nINDIA",
                            "address_position": "left",
                            "country": "CH",
                            "delivery_product": "cheap",
                            "print_mode": "simplex",
                            "print_spectrum": "grayscale",
                            "price_currency": False,
                            "price_value": False,
                            "paper_types": ["normal"],
                            "source": "api",
                            "tracking_number": False,
                            "submitted_at": False,
                            "created_at": "2023-05-19T09:34:31+0200",
                            "updated_at": "2023-05-19T09:34:33+0200",
                        },
                    },
                    *(events or []),
                ],
            }
        )

    def _post_webhook(self, route, body, secret=WEBHOOK_SECRET):
        signature = hmac.new(
            secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return self.url_open(
            route,
            data=body,
            headers={"Signature": signature, "Content-Type": "application/json"},
        )

    def _pushed_document(self, uuid="ddd105d8-42f6-4357-a103-9b2449bbd8e2"):
        """A pingen.document already on pingen.com, without any network call."""
        attachment = self.env["ir.attachment"].create(
            {
                "name": "letter.pdf",
                "datas": base64.b64encode(b"%PDF-1.4"),
                "type": "binary",
            }
        )
        attachment.write({"send_to_pingen": True})
        document = attachment.pingen_document_ids
        document.write({"state": "pushed", "pingen_uuid": uuid})
        return document

    def _layout_document(self, restricted=False):
        with pymupdf.open() as pdf:
            page = pdf.new_page(width=595, height=842)
            if restricted:
                page.draw_rect((5, 100, 10, 120), color=None, fill=(0, 0, 0))
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "layout.pdf",
                    "datas": base64.b64encode(pdf.tobytes()),
                    "type": "binary",
                    "company_id": self.company.id,
                }
            )
        attachment.write({"send_to_pingen": True})
        return attachment.pingen_document_ids

    def test_layout_error_prevents_upload(self):
        document = self._layout_document(restricted=True)
        client = MagicMock()
        with (
            patch.object(type(self.company), "_get_pingen_client", return_value=client),
            patch("odoo.addons.pingen.models.pingen_document.Registry") as registry,
        ):
            # Exercise the error-write path in the test transaction: a separate
            # cursor cannot see this uncommitted test document.
            registry.return_value.cursor.return_value.__enter__.return_value = (
                self.env.cr
            )
            with self.assertRaisesRegex(UserError, "page 1: left margin"):
                document.push_to_pingen()
        document.invalidate_recordset()
        self.assertEqual(document.state, "pingen_error")
        self.assertIn("page 1: left margin", document.last_error_message)
        client.push_document.assert_not_called()

    def test_clean_layout_preserves_upload(self):
        document = self._layout_document()
        client = MagicMock()
        client.push_document.return_value = (
            "letter-id",
            "post-id",
            {"status": "valid"},
        )
        with patch.object(
            type(self.company), "_get_pingen_client", return_value=client
        ):
            self.assertTrue(document.push_to_pingen())
        client.push_document.assert_called_once()
        args = client.push_document.call_args.args
        self.assertEqual(args[0], "layout.pdf")
        self.assertTrue(args[1].getvalue().startswith(b"%PDF"))
        self.assertEqual(args[2], "application/pdf")
        self.assertEqual(document.state, "pushed")
        self.assertEqual(document.pingen_uuid, "letter-id")
        self.assertFalse(document.last_error_message)

    def test_pingen_push_document(self):
        with (
            vcr_pingen.use_cassette("test_pingen_push_document"),
            freeze_time("2023-05-19"),
        ):
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "in_invoice_yourcompany_demo.pdf",
                    "datas": base64.b64encode(bytes("", "utf8")),
                    "type": "binary",
                }
            )
            attachment.write({"send_to_pingen": True})
            pingen_document = attachment.pingen_document_ids
            pingen_document.push_to_pingen()
        self.assertEqual(pingen_document.state, "pushed")
        self.assertTrue(pingen_document.pingen_uuid)

        # as the demo invoice report does not meet pingen requirements,
        # pingen will notify us about it on letter_issues webhook, signed with
        # the company secret
        response = self._post_webhook(
            "/pingen/letter_issues",
            self.get_request_json(pingen_document.pingen_uuid),
        )
        self.assertEqual(response.status_code, 200)
        pingen_document.invalidate_recordset()
        self.assertEqual(pingen_document.state, "pingen_error")
        self.assertEqual(pingen_document.last_error_message, "Validation failed")

    def test_webhook_rejects_bad_signature(self):
        document = self._pushed_document()
        response = self._post_webhook(
            "/pingen/letter_issues",
            self.get_request_json(document.pingen_uuid),
            secret="not-the-company-secret",
        )
        self.assertEqual(response.status_code, 403)
        document.invalidate_recordset()
        self.assertEqual(document.state, "pushed")

    def test_webhook_sent_without_distributor_event(self):
        # No `transferred_to_distributor` event: used to crash on an empty date.
        document = self._pushed_document()
        response = self._post_webhook(
            "/pingen/sent_letters", self.get_request_json(document.pingen_uuid)
        )
        self.assertEqual(response.status_code, 200)
        document.invalidate_recordset()
        self.assertEqual(document.state, "sent")

    def test_webhook_sent_with_distributor_event(self):
        document = self._pushed_document()
        event = {
            "type": "letters_events",
            "id": "e1",
            "attributes": {
                "code": "transferred_to_distributor",
                "emitted_at": "2023-05-20T10:00:00+0200",
            },
        }
        response = self._post_webhook(
            "/pingen/delivered_letters",
            self.get_request_json(document.pingen_uuid, events=[event]),
        )
        self.assertEqual(response.status_code, 200)
        document.invalidate_recordset()
        self.assertEqual(document.state, "sent")
        self.assertEqual(document.send_date, datetime(2023, 5, 20, 8, 0))

    def test_prepare_values_statuses(self):
        document_model = self.env["pingen.document"]
        delivered = document_model._prepare_values_from_post_infos(
            {"status": "delivered", "submitted_at": "2023-05-20T10:00:00+0200"}
        )
        self.assertEqual(delivered["state"], "sent")
        self.assertEqual(delivered["send_date"], "2023-05-20 08:00:00")
        undeliverable = document_model._prepare_values_from_post_infos(
            {"status": "undeliverable"}
        )
        self.assertEqual(undeliverable["state"], "error_undeliverable")
        cancelled = document_model._prepare_values_from_post_infos(
            {"status": "cancelled"}
        )
        self.assertEqual(cancelled["state"], "canceled")
        unknown = document_model._prepare_values_from_post_infos({"status": "valid"})
        self.assertNotIn("state", unknown)
        self.assertFalse(unknown["send_date"])
        # Nothing received at all must not crash.
        self.assertNotIn("state", document_model._prepare_values_from_post_infos(None))

    def test_token_cache_is_per_client(self):
        future = (datetime.now() + timedelta(hours=12)).timestamp()
        tokens = iter(["token-a", "token-b"])

        def fake_fetch(pingen):
            return {
                "token_type": "Bearer",
                "access_token": next(tokens),
                "expires_at": future,
            }

        with patch.object(Pingen, "_fetch_token", fake_fetch):
            first = Pingen("client-a", "secret-a", ORGANISATION, staging=True)
            second = Pingen("client-b", "secret-b", ORGANISATION, staging=True)
            self.assertEqual(first.session.headers["Authorization"], "Bearer token-a")
            self.assertEqual(second.session.headers["Authorization"], "Bearer token-b")
            # A second session of the first client reuses its cached token.
            again = Pingen("client-a", "secret-a", ORGANISATION, staging=True)
            self.assertEqual(again.session.headers["Authorization"], "Bearer token-a")

    def test_letter_calls_use_deliveries_endpoints_and_idempotency(self):
        pingen = Pingen(
            "client", "secret", ORGANISATION, staging=True, address_position="right"
        )
        Pingen.token_registry[pingen._token_key] = {
            "token": "Bearer t",
            "expiry": datetime.now() + timedelta(hours=1),
        }
        session = MagicMock()
        response = MagicMock(ok=True, content=b"{}")
        response.json.return_value = {
            "data": {"id": "L1", "attributes": {"url": "u", "url_signature": "s"}}
        }
        session.get.return_value = response
        session.post.return_value = response
        session.patch.return_value = response
        pingen._session = session
        with patch("odoo.addons.pingen.models.pingen.requests.put") as put:
            put.return_value = MagicMock(ok=True)
            pingen.push_document("letter.pdf", MagicMock(), "application/pdf")
        pingen.send_document("L1", "fast", "grayscale", "simplex")

        post_url = session.post.call_args.args[0]
        self.assertEqual(
            post_url,
            f"https://api-staging.pingen.com/organisations/{ORGANISATION}"
            "/deliveries/letters",
        )
        self.assertTrue(session.post.call_args.kwargs["headers"]["Idempotency-Key"])
        payload = json.loads(session.post.call_args.kwargs["data"])
        self.assertEqual(payload["data"]["attributes"]["address_position"], "right")
        self.assertIs(payload["data"]["attributes"]["auto_send"], False)
        patch_url = session.patch.call_args.args[0]
        self.assertTrue(patch_url.endswith("/deliveries/letters/L1/send"))
        self.assertTrue(session.patch.call_args.kwargs["headers"]["Idempotency-Key"])
        self.assertTrue(all("timeout" in c.kwargs for c in session.post.call_args_list))

    def test_decoded_content_of_url_attachment(self):
        attachment = self.env["ir.attachment"].create(
            {"name": "remote.pdf", "type": "url", "url": "https://example.com/x.pdf"}
        )
        with patch("odoo.addons.pingen.models.ir_attachment.requests.get") as get:
            get.return_value = MagicMock(ok=True, content=b"%PDF-remote")
            self.assertEqual(attachment._decoded_content(), b"%PDF-remote")

    def test_update_cron_skips_documents_never_pushed(self):
        attachment = self.env["ir.attachment"].create(
            {
                "name": "pending.pdf",
                "datas": base64.b64encode(b"%PDF"),
                "type": "binary",
            }
        )
        attachment.write({"send_to_pingen": True})
        with patch.object(Pingen, "post_infos") as post_infos:
            self.env["pingen.document"]._update_post_infos_cron()
        post_infos.assert_not_called()

    def test_credentials_hidden_from_non_admin(self):
        fields = self.env["res.company"].fields_get()
        for name in (
            "pingen_clientid",
            "pingen_client_secretid",
            "pingen_webhook_secret",
        ):
            self.assertEqual(
                self.env["res.company"]._fields[name].groups, "base.group_system"
            )
        self.assertIn("pingen_organization", fields)

    def test_refresh_letter_quote(self):
        document = self._pushed_document()
        document.write(
            {
                "delivery_product": "registered",
                "print_mode": "duplex",
                "print_spectrum": "color",
            }
        )
        client = MagicMock()
        client.post_infos.return_value = {
            "status": "valid",
            "country": "CH",
            "address": "Test address",
            "file_pages": 2,
            "paper_types": ["normal", "payment_slip"],
        }
        client.price_quote.return_value = (4.25, "USD")
        document._get_and_update_post_infos(client)
        client.post_infos.assert_called_once_with(document.pingen_uuid)
        client.price_quote.assert_called_once_with(
            country="CH",
            delivery_product="registered",
            print_mode="duplex",
            print_spectrum="color",
            paper_types=["normal", "payment_slip"],
        )
        self.assertEqual(document.estimated_cost, 4.25)
        self.assertEqual(document.currency_id.name, "USD")
        self.assertEqual(document.country_id.code, "CH")
        self.assertEqual(document.pages, 2)
        self.assertEqual(document.parsed_address, "Test address")
        self.assertFalse(document.cost)

    def test_refresh_letter_without_quote(self):
        document = self._pushed_document()
        client = MagicMock()
        for infos, state in (
            ({"price_value": 3.5, "price_currency": "USD"}, "pushed"),
            ({"status": "validating"}, "pushed"),
            ({"country": "CH", "file_pages": 1}, "sendcenter"),
            ({"country": "CH", "file_pages": 1, "status": "delivered"}, "pushed"),
        ):
            with self.subTest(infos=infos, state=state):
                document.write({"state": state})
                client.post_infos.return_value = infos
                document._refresh_letter_infos(client)
                client.price_quote.assert_not_called()

    def test_refresh_clears_stale_estimate_when_quote_fails(self):
        document = self._pushed_document()
        client = MagicMock()
        client.post_infos.return_value = {"country": "CH", "file_pages": 1}
        client.price_quote.return_value = (3.0, "USD")
        document._refresh_letter_infos(client)
        self.assertEqual(document.estimated_cost, 3.0)
        self.assertEqual(document.currency_id.name, "USD")
        client.price_quote.side_effect = RuntimeError("calculator unavailable")
        document._refresh_letter_infos(client)
        self.assertFalse(document.estimated_cost)
        self.assertFalse(document.currency_id)

    def test_refresh_cron_action_calls_its_method(self):
        cron = self.env.ref("pingen.ir_cron_refresh_pingen_pushed")
        with patch.object(
            type(self.env["pingen.document"]), "_refresh_pushed_documents_cron"
        ) as refresh:
            cron.ir_actions_server_id.run()
        refresh.assert_called_once_with()

    def test_refresh_letter_paper_types_fallback(self):
        document = self._pushed_document()
        client = MagicMock()
        client.price_quote.return_value = (2, "USD")
        for paper_types in (None, [], ["normal"]):
            with self.subTest(paper_types=paper_types):
                client.post_infos.return_value = {
                    "country": "CH",
                    "file_pages": 2,
                    "paper_types": paper_types,
                }
                document._refresh_letter_infos(client)
                self.assertEqual(
                    client.price_quote.call_args.kwargs["paper_types"],
                    ["normal", "normal"],
                )

    def test_refresh_letter_quote_failure(self):
        document = self._pushed_document()
        client = MagicMock()
        client.post_infos.return_value = {"country": "CH", "file_pages": 1}
        client.price_quote.side_effect = RuntimeError("calculator unavailable")
        document._refresh_letter_infos(client)
        self.assertFalse(document.estimated_cost)
        self.assertEqual(document.pages, 1)

    def test_push_refresh_is_best_effort(self):
        for error in (None, RuntimeError("read unavailable")):
            with self.subTest(error=error):
                document = self._layout_document()
                client = MagicMock()
                client.push_document.return_value = ("L1", False, {"status": "valid"})
                with patch.object(
                    type(document), "_refresh_letter_infos", side_effect=error
                ) as refresh:
                    document._push_to_pingen(client)
                refresh.assert_called_once_with(client)
                self.assertEqual(document.state, "pushed")
                self.assertEqual(document.pingen_uuid, "L1")

    def test_refresh_pushed_cron_filters_and_continues(self):
        first = self._pushed_document("L1")
        second = self._pushed_document("L2")
        excluded = self._pushed_document("L3")
        excluded.write({"state": "sent"})
        pending = self._pushed_document("L4")
        pending.write({"state": "pending"})
        processed = []

        def refresh(document, client):
            processed.append(document.id)
            if len(processed) == 1:
                raise RuntimeError("read unavailable")

        with (
            patch("odoo.addons.pingen.models.pingen_document.Registry") as registry,
            patch.object(type(first), "_refresh_letter_infos", refresh),
            patch.object(
                type(self.company), "_get_pingen_client", return_value=MagicMock()
            ),
        ):
            # Let the new environment see this transaction's uncommitted records.
            registry.return_value.cursor.return_value.__enter__.return_value = (
                self.env.cr
            )
            self.env["pingen.document"]._refresh_pushed_documents_cron()
        self.assertCountEqual(processed, [first.id, second.id])

    def test_price_quote_payload_and_response(self):
        client = Pingen("client", "secret", ORGANISATION)
        client._session = MagicMock()
        response = MagicMock()
        with patch.object(client, "_send", return_value=response) as send:
            response.json.return_value = {
                "data": {"attributes": {"price": 3.25, "currency": "USD"}}
            }
            self.assertEqual(
                client.price_quote("CH", "registered", "simplex", "color", ["normal"]),
                (3.25, "USD"),
            )
            self.assertEqual(send.call_args.args[0], client._session.post)
            self.assertEqual(
                send.call_args.args[1], client.letters_url + "/price-calculator"
            )
            self.assertEqual(
                json.loads(send.call_args.kwargs["data"]),
                {
                    "data": {
                        "type": "letter_price_calculator",
                        "attributes": {
                            "country": "CH",
                            "delivery_product": "registered",
                            "print_mode": "simplex",
                            "print_spectrum": "color",
                            "paper_types": ["normal"],
                        },
                    }
                },
            )
            self.assertIn("Content-Type", send.call_args.kwargs["headers"])
            for price in (None, 0, -1, "3.25", True, float("inf"), float("nan")):
                with self.subTest(price=price):
                    attributes = {} if price is None else {"price": price}
                    response.json.return_value = {"data": {"attributes": attributes}}
                    self.assertEqual(
                        client.price_quote(
                            "CH", "cheap", "simplex", "color", ["normal"]
                        ),
                        (None, None),
                    )
