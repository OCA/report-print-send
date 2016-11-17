# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import errno
import logging
import os

from openerp import models, fields, api

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
            if err.errno == errno.ENOENT:
                pass
            raise
        if not option:
            return vals

        vals_trays = []

        tray_names = set(tray.system_name for tray in self.tray_ids)
        for tray_option in option.choices:
            if tray_option['choice'] not in tray_names:
                tray_vals = {
                    'name': tray_option['text'],
                    'system_name': tray_option['choice'],
                }
                vals_trays.append((0, 0, tray_vals))

        cups_trays = set(tray_option['choice'] for tray_option
                         in option.choices)
        for tray in self.tray_ids:
            if tray.system_name not in cups_trays:
                vals_trays.append((2, tray.id))

        vals['tray_ids'] = vals_trays
        return vals

    @api.multi
    def print_options(self, report=None, format=None, copies=1):
        """ Hook to define Tray """
        printing_act_obj = self.env['printing.report.xml.action']
        options = super(PrintingPrinter, self).print_options(report, format)

        # Retrieve user default values
        tray = self.env.user.printer_tray_id

        if report is not None:
            # Retrieve report default values
            if report.printer_tray_id:
                tray = report.printer_tray_id

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
