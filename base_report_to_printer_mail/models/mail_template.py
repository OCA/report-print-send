from odoo import models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def _generate_template(
        self,
        res_ids,
        render_fields,
        recipients_allow_suggested=False,
        find_or_create_partners=False,
    ):
        self = self.with_context(must_skip_send_to_printer=True)
        return super()._generate_template(
            res_ids,
            render_fields,
            recipients_allow_suggested=recipients_allow_suggested,
            find_or_create_partners=find_or_create_partners,
        )
