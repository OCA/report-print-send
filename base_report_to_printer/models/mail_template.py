# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def generate_email(self, res_ids, fields):
        """Ensure that any report rendered to send it by email not is sent to printer
        directly if the report is setting to send it to printer.
        For example, user set delivery slip report redirect to printer and
        'Send an email when picking is validated' is active, if we do not inject this
        context the report will be send twice to printer.
        """
        return super(
            MailTemplate, self.with_context(must_skip_send_to_printer=True)
        ).generate_email(res_ids, fields)
