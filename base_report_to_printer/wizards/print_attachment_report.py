# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import base64

from odoo import _, fields, models


class PrintAttachment(models.TransientModel):
    _name = "wizard.print.attachment"
    _description = "Print Attachment"

    printer_id = fields.Many2one(
        comodel_name="printing.printer",
        string="Printer",
        required=True,
        help="Printer used to print the attachments.",
    )
    attachment_line_ids = fields.One2many(
        "wizard.print.attachment.line",
        "wizard_id",
        string="Attachments to print",
    )

    def print_attachments(self):
        """Prints a label per selected record"""
        self.ensure_one()
        errors = []
        for att_line in self.attachment_line_ids:
            data = att_line.attachment_id.datas
            title = att_line.attachment_id.store_fname
            if not data:
                errors.append(att_line)
                continue
            content = base64.b64decode(data)
            content_format = att_line.get_format()
            self.printer_id.print_document(
                None,
                content=content,
                format=content_format,
                copies=att_line.copies,
                title=title,
            )
        if errors:
            return {
                "warning": _(
                    "Following attachments could not be printed:\n\n%s"
                    % "\n".join(
                        [
                            _("%s (%s copies)") % (err.record_name, err.copies)
                            for err in errors
                        ]
                    )
                )
            }


class PrintAttachmentLine(models.TransientModel):
    _name = "wizard.print.attachment.line"
    _description = "Print Attachment line"

    wizard_id = fields.Many2one("wizard.print.attachment")
    attachment_id = fields.Many2one(
        "ir.attachment",
        required=True,
        domain=[
            "|",
            ("mimetype", "=", "application/pdf"),
            ("mimetype", "=", "application/octet-stream"),
        ],
    )
    record_name = fields.Char(related="attachment_id.res_name", readonly=True)
    copies = fields.Integer(default=1)

    def get_format(self):
        self.ensure_one()
        mimetype = self.attachment_id.mimetype
        if mimetype == "application/pdf":
            return "pdf"
        else:
            return "raw"
