# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import base64

from openerp import models, api, fields


class PrintAttachment(models.TransientModel):
    _name = 'wizard.print.attachment'
    _description = 'Print Attachment'

    printer_id = fields.Many2one(
        comodel_name='printing.printer', string='Printer', required=True,
        help='Printer used to print the attachments.'
    )
    attachment_line_ids = fields.One2many(
        'wizard.print.attachment.line', 'wizard_id',
        string='Attachments to print',
    )

    @api.multi
    def print_attachments(self):
        """ Prints a label per selected record """
        self.ensure_one()
        for att_line in self.attachment_line_ids:
            content = base64.b64decode(att_line.attachment_id.datas)
            content_format = att_line.get_format()
            self.printer_id.print_document(
                None,
                content=content,
                format=content_format,
                copies=att_line.copies
            )
        self.attachment_line_ids.unlink()


class PrintAttachment(models.TransientModel):
    _name = 'wizard.print.attachment.line'
    _description = 'Print Attachment line'

    wizard_id = fields.Many2one("wizard.print.attachment")
    attachment_id = fields.Many2one(
        'ir.attachment',
        domain="['|', ('mimetype', '=', 'application/pdf'), ('mimetype', '=', 'application/octet-stream')]"
    )
    record_name = fields.Char(related="attachment_id.res_name", readonly=True)
    copies = fields.Integer(default=1)

    @api.multi
    def get_format(self):
        self.ensure_one()
        mimetype = self.attachment_id.mimetype
        if mimetype == "application/pdf":
            return "pdf"
        else:
            return 'raw'
