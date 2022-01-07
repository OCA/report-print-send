# Copyright (C) 2022 PESOL (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from OpenSSL import crypto

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
        key = config_param_sudo.get_param("qz.key", default=False)
        password = None
        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, key, password)
        sign = crypto.sign(pkey, kwargs.get("request", ""), "sha512")
        data_base64 = base64.b64encode(sign)
        return request.make_response(data_base64, [("Content-Type", "text/plain")])
