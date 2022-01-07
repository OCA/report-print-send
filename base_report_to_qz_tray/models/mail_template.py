# Copyright (C) 2022 PESOL (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def generate_email(self, res_ids, fields=None):
        return super(
            MailTemplate, self.with_context(must_skip_send_to_printer=True)
        ).generate_email(res_ids, fields=fields)
