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

    input_tray_ids = fields.One2many(comodel_name='printing.tray.input',
                                     inverse_name='printer_id',
                                     string='Paper Sources',
                                     oldname='tray_ids')

    output_tray_ids = fields.One2many(comodel_name='printing.tray.output',
                                      inverse_name='printer_id',
                                      string='Output trays')

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
        input_options = ppd.findOption('InputSlot')
        output_options = ppd.findOption('OutputBin')

        try:
            os.unlink(ppd_path)
        except OSError as err:
            # ENOENT means No such file or directory
            # The file has already been deleted, we can continue the update
            if err.errno != errno.ENOENT:
                raise

        if input_options:
            vals['input_tray_ids'] = [
                (0, 0, {'name': opt['text'], 'system_name': opt['choice']})
                for opt in input_options.choices
                if opt['choice'] not in self.input_tray_ids.mapped('system_name')
            ]
            trays = [opt['choice'] for opt in input_options.choices]
            vals['input_tray_ids'].extend([
                (2, tray.id)
                for tray in self.input_tray_ids
                if tray.system_name not in trays
            ])

        if output_options:
            vals['output_tray_ids'] = [
                (0, 0, {'name': opt['text'], 'system_name': opt['choice']})
                for opt in output_options.choices
                if opt['choice'] not in self.output_tray_ids.mapped('system_name')
            ]
            trays = [opt['choice'] for opt in output_options.choices]
            vals['output_tray_ids'].extend([
                (2, tray.id)
                for tray in self.output_tray_ids
                if tray.system_name not in trays
            ])

        return vals

    @api.multi
    def print_options(self, report=None, format=None, copies=1):
        """ Hook to define Tray """
        printing_act_obj = self.env['printing.report.xml.action']
        options = super(PrintingPrinter, self).print_options(report, format)

        if report is not None:
            full_report = self.env['report']._get_report_from_name(report) \
                if isinstance(report, basestring) else report

            in_tray = (full_report.printer_input_tray_id or
                       self.env.user.printer_input_tray_id).system_name

            out_tray = (full_report.printer_output_tray_id or
                        self.env.user.printer_output_tray_id).system_name

            # Retrieve report-user/language specific values
            print_action = printing_act_obj.search(
                [('report_id', '=', full_report.id),
                 '|', ('user_id', '=', self.env.uid),
                 ('language_id.code', '=', self.env.lang),
                 ('action', '!=', 'user_default')])
            if print_action:
                user_action = print_action.behaviour()
            if user_action.get('input_tray'):
                in_tray = user_action['input_tray']
            if user_action.get('output_tray'):
                out_tray = user_action['output_tray']

            options['InputSlot'] = in_tray
            options['OutputBin'] = out_tray

        return options
