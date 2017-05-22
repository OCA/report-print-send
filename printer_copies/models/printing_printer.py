# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    import cups
except ImportError:
    _logger.debug('Cannot `import cups`.')


class PrintingPrinter(models.Model):
    _inherit = 'printing.printer'
    copies = fields.Integer(
        string='Copies',
        default=1
    )

    @api.multi
    def print_options(self, report=None, format=None, copies=1):
        """ Hook to define Tray """
        printing_act_obj = self.env['printing.report.xml.action']

        if report is not None:
            # Retrieve report default values
            if report.copies:
                copies = report.copies
            else:
                # Retrieve user default values
                copies = self.env.user.copies

            # Retrieve report-user specific values
            action = printing_act_obj.search([
                ('report_id', '=', report.id),
                ('user_id', '=', self.env.uid),
                ('action', '!=', 'user_default'),
            ], limit=1)
            if action.copies:
                copies = action.copies

        options = super(PrintingPrinter, self).print_options(report=report,
                                                             format=format,
                                                             copies=copies)
        return options
