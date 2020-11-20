# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from collections import OrderedDict

from odoo import fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    only_even_total_page = fields.Boolean(
        help="A blank page is added if report has an odd page total.\n"
        "Really helpful when your document is printed recto/verso.\n"
    )
    even_total_page_behavior = fields.Boolean(
        compute="_compute_custom_even_total_page_behavior"
    )

    def _compute_custom_even_total_page_behavior(self):
        """Override to set your custom behavior"""
        for rec in self:
            rec.even_total_page_behavior = rec.only_even_total_page

    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        old_attachment_value = self.attachment
        if self.even_total_page_behavior:
            # requrired to trigger postprocess_pdf_report() hook
            self.attachment = True
            save_in_attachment = OrderedDict()
        result = super()._post_pdf(
            save_in_attachment, pdf_content=pdf_content, res_ids=res_ids
        )
        # We restore original state
        self.attachment = old_attachment_value
        return result

    # def postprocess_pdf_report(self, record, buffer):
    #     reader = PdfFileReader(buffer)
    #     # buffer.seek(0); buffer.readlines()[-5:]
    #     writer = PdfFileWriter()
    #     # import pdb; pdb.set_trace()
    #     if reader.getNumPages():
    #     # if reader.getNumPages() % 2 != 0:
    #         writer.appendPagesFromReader(reader)
    #         # buffer.seek(0); buffer.readlines()[-5:]
    #     return super().postprocess_pdf_report(record, buffer)

