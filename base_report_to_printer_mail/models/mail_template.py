from odoo import models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def generate_email(self, res_ids, fields=None):
        return super(MailTemplate, self.with_context(
            must_skip_send_to_printer=True
        )).generate_email(res_ids, fields=fields)
