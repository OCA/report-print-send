# Copyright (C) 2022 PESOL (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def _generate_template(self, res_ids, fields=None):
        # Pre-V17
        return super(
            MailTemplate, self.with_context(must_skip_send_to_printer=True)
        ).generate_email(res_ids, fields=fields)
        # V17 onwards
        # return super(
        #     MailTemplate, self.with_context(must_skip_send_to_printer=True)
        # )._generate_template(
        #     res_ids,
        #     render_fields=render_fields,
        #     find_or_create_partners=find_or_create_partners,
        # )
