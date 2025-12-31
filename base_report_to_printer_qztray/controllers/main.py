# Copyright (C) 2022 PESOL (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from odoo import http
from odoo.http import request


class SignMessage(http.Controller):
    @http.route("/qz-certificate/", auth="public")
    def qz_certificate(self, **kwargs):
        config_param_sudo = request.env["ir.config_parameter"].sudo()
        cert = config_param_sudo.get_param("qz.certificate", default=False)
        return request.make_response(cert, [("Content-Type", "text/plain")])

    @http.route("/qz-sign-message/", auth="public")
    def qz_sign_message(self, **kwargs):
        config_param_sudo = request.env["ir.config_parameter"].sudo()
        key_pem = config_param_sudo.get_param("qz.key", default=False)
        private_key = serialization.load_pem_private_key(
            key_pem.encode("utf-8"), password=None, backend=default_backend()
        )
        message = kwargs.get("request", "").encode("utf-8")
        signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA512())
        data_base64 = base64.b64encode(signature)
        return request.make_response(data_base64, [("Content-Type", "text/plain")])
