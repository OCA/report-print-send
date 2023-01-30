# Copyright 2012-2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
import json
import logging
from os.path import dirname, join
from unittest.mock import patch

from freezegun import freeze_time
from vcr import VCR

from odoo.tests import tagged
from odoo.tests.common import HttpCase

from odoo.addons.website.tools import MockRequest

from ..controllers.main import PingenController

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


@tagged("post_install", "-at_install")
class TestPingen(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.user.company_id
        cls.company.pingen_clientid = "1234"
        cls.company.pingen_client_secretid = "1234567893"
        cls.company.pingen_organization = "4c08c24e-65f8-47cf-b280-518ee76e3437"
        cls.company.pingen_staging = True

        cls.pc = PingenController()

    # flake8: noqa: B950
    def get_request_json(self, uuid):
        return json.dumps(
            {
                "data": {
                    "type": "webhook_issues",
                    "id": "735582d1-ccdf-423a-b493-1b3a6935df29",
                    "attributes": {
                        "reason": "Validation failed",
                        "url": r"https:\/\/36f4-2a02-1210-3497-c400-296e-3b7-6940-e38b.ngrok-free.app\/\/pingen\/letter_issues",
                        "created_at": "2023-05-19T09:35:01+0200",
                    },
                    "relationships": {
                        "organisation": {
                            "links": {
                                "related": r"https:\/\/identity-staging.pingen.com\/organisations\/4c08c24e-65f8-47cf-b280-518ee76e3437"
                            },
                            "data": {
                                "type": "organisations",
                                "id": "4c08c24e-65f8-47cf-b280-518ee76e3437",
                            },
                        },
                        "letter": {
                            "links": {
                                "related": r"https:\/\/identity-staging.pingen.com\/organisations\/4c08c24e-65f8-47cf-b280-518ee76e3437\/letters\/ddd105d8-42f6-4357-a103-9b2449bbd8e2"
                            },
                            "data": {
                                "type": "letters",
                                "id": uuid,
                            },
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
                        "type": "organisations",
                        "id": "4c08c24e-65f8-47cf-b280-518ee76e3437",
                        "attributes": {
                            "name": "c2c",
                            "status": "active",
                            "plan": "free",
                            "billing_mode": "prepaid",
                            "billing_currency": "CHF",
                            "billing_balance": 199995.56,
                            "default_country": "CH",
                            "default_address_position": "right",
                            "data_retention_addresses": 6,
                            "data_retention_pdf": 1,
                            "color": "#0758FF",
                            "created_at": "2022-10-19T16:08:17+0200",
                            "updated_at": "2023-02-24T14:06:17+0100",
                        },
                        "links": {
                            "self": r"https:\/\/identity-staging.pingen.com\/organisations\/4c08c24e-65f8-47cf-b280-518ee76e3437"
                        },
                    },
                    {
                        "type": "letters",
                        "id": "ddd105d8-42f6-4357-a103-9b2449bbd8e2",
                        "attributes": {
                            "status": "action_required",
                            "file_original_name": "in_invoice_yourcompany_demo.pdf",
                            "file_pages": 1,
                            "address": "405 Pushp Business Campus\n,\nhmedabad, Gujarat, 382418\nnfo@azureinterior.com\n+92 7405987125",
                            "address_position": "left",
                            "country": "CH",
                            "delivery_product": "cheap",
                            "print_mode": "simplex",
                            "print_spectrum": "grayscale",
                            "price_currency": False,
                            "price_value": False,
                            "paper_types": ["normal"],
                            "fonts": [
                                {
                                    "name": "LiberationSans",
                                    "is_embedded": True,
                                },
                                {
                                    "name": "Tibetan_Machine_Uni",
                                    "is_embedded": True,
                                },
                                {
                                    "name": "Chandas",
                                    "is_embedded": True,
                                },
                                {
                                    "name": "DejaVuSans-Bold",
                                    "is_embedded": True,
                                },
                                {
                                    "name": "DejaVuSans",
                                    "is_embedded": True,
                                },
                            ],
                            "source": "api",
                            "tracking_number": False,
                            "submitted_at": False,
                            "created_at": "2023-05-19T09:34:31+0200",
                            "updated_at": "2023-05-19T09:34:33+0200",
                        },
                        "links": {
                            "self": r"https:\/\/identity-staging.pingen.com\/organisations\/4c08c24e-65f8-47cf-b280-518ee76e3437\/letters\/ddd105d8-42f6-4357-a103-9b2449bbd8e2"
                        },
                    },
                    {
                        "type": "letters_events",
                        "id": "a9612d08-81c0-4259-8b0a-648c85377f71",
                        "attributes": {
                            "code": "content_failed_inspection",
                            "name": "Validation failed",
                            "producer": "Pingen",
                            "location": "",
                            "has_image": False,
                            "data": [],
                            "emitted_at": "2023-05-19T09:34:33+0200",
                            "created_at": "2023-05-19T09:34:33+0200",
                            "updated_at": "2023-05-19T09:34:33+0200",
                        },
                    },
                ],
            }
        )

    @vcr_pingen.use_cassette
    @freeze_time("2023-05-19")
    def test_pingen_push_document(self):
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

        # as the demo invoice report does not meet pingen requirements,
        # pingen will notify us about it on letter_issues webhook

        with patch(
            "odoo.addons.pingen.controllers.main.PingenController._get_request_content"
        ) as mocked_function, MockRequest(self.env) as mock_request:
            mocked_function.return_value = self.get_request_json(
                pingen_document.pingen_uuid
            )
            mock_request.httprequest.method = "POST"
            # avoid checking signature when calling webhooks
            with patch(
                "odoo.addons.pingen.controllers.main.PingenController._verify_signature"
            ) as mocked_verify_sign:
                mocked_verify_sign.return_value = True
                self.pc.letter_issues()

        self.assertEqual(pingen_document.state, "pingen_error")
        self.assertEqual(pingen_document.last_error_message, "Validation failed")
