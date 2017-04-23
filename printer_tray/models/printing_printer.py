# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import errno
import logging
import os

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    import cups
except ImportError:
    _logger.debug('Cannot `import cups`.')


class PrintingPrinter(models.Model):
    _inherit = 'printing.printer'

    tray_ids = fields.One2many(comodel_name='printing.tray',
                               inverse_name='printer_id',
                               string='Paper Sources')

    @api.multi
    def _prepare_update_from_cups(self, cups_connection, cups_printer):
        vals = super(PrintingPrinter, self)._prepare_update_from_cups(
            cups_connection, cups_printer)

        printer_uri = cups_printer['printer-uri-supported']
        printer_system_name = printer_uri[printer_uri.rfind('/') + 1:]
        ppd_info = cups_connection.getPPD3(printer_system_name)
        ppd_path = ppd_info[2]
        if not ppd_path:
            return vals

        ppd = cups.PPD(ppd_path)
        option = ppd.findOption('InputSlot')
        try:
            os.unlink(ppd_path)
        except OSError as err:
            # ENOENT means No such file or directory
            # The file has already been deleted, we can continue the update
            if err.errno != errno.ENOENT:
                raise
        if not option:
            return vals

        vals['tray_ids'] = []
        cups_trays = {
            tray_option['choice']: tray_option['text']
            for tray_option in option.choices
        }

        # Add new trays
        vals['tray_ids'].extend([
            (0, 0, {'name': text, 'system_name': choice})
            for choice, text in cups_trays.items()
            if choice not in self.tray_ids.mapped('system_name')
        ])

        # Remove deleted trays
        vals['tray_ids'].extend([
            (2, tray.id)
            for tray in self.tray_ids.filtered(
                lambda record: record.system_name not in cups_trays.keys())
        ])

        return vals

    @api.multi
    def print_options(self, report=None, format=None, copies=1):
        """ Hook to define Tray """
        printing_act_obj = self.env['printing.report.xml.action']
        options = super(PrintingPrinter, self).print_options(report, format)

        if report is not None:
            # Retrieve report default values
            if report.printer_tray_id:
                tray = report.printer_tray_id
            else:
                # Retrieve user default values
                tray = self.env.user.printer_tray_id

            # Retrieve report-user specific values
            action = printing_act_obj.search([
                ('report_id', '=', report.id),
                ('user_id', '=', self.env.uid),
                ('action', '!=', 'user_default'),
            ], limit=1)
            if action.printer_tray_id:
                tray = action.printer_tray_id

            if tray:
                options['InputSlot'] = str(tray.system_name)

        return options
