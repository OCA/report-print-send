# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class PrintingPrinter(models.Model):
    _inherit = 'printing.printer'

    @api.multi
    def print_document(self, report, content, **print_opts):
        self.ensure_one()
        content = content.encode('utf-8')
        return super(PrintingPrinter, self).print_document(report, content,
                                                           **print_opts)
