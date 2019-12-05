# Copyright 2019 Compassion
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

    printer_options = fields.One2many(
        comodel_name='printer.option',
        inverse_name='printer_id',
        readonly=True)
    printer_option_choices = fields.One2many(
        comodel_name='printer.option.choice',
        inverse_name='printer_id',
        string='Option Choices',
        readonly=True)

    def _get_cups_ppd(self, cups_connection, cups_printer):
        """ Returns a PostScript Printer Description (PPD) file for the
        printer. """
        printer_uri = cups_printer['printer-uri-supported']
        printer_system_name = printer_uri[printer_uri.rfind('/') + 1:]
        ppd_info = cups_connection.getPPD3(printer_system_name)
        ppd_path = ppd_info[2]
        if not ppd_path:
            return False, False
        return ppd_path, cups.PPD(ppd_path)

    def _cleanup_ppd(self, ppd_path):
        try:
            os.unlink(ppd_path)
        except OSError as err:
            # ENOENT means No such file or directory
            # The file has already been deleted, we can continue the update
            if err.errno != errno.ENOENT:
                raise

    @api.multi
    def _prepare_update_from_cups(self, cups_connection, cups_printer):
        vals = super()._prepare_update_from_cups(
            cups_connection, cups_printer)

        current_option_keys = self.printer_option_choices.mapped(
            'composite_key')
        ppd_path, ppd = self._get_cups_ppd(cups_connection, cups_printer)
        if ppd_path and ppd:
            self._load_printer_option_list(ppd)

            new_option_values = []
            for printer_option in self.printer_options:
                option_key = printer_option.option_key
                new_options = self.discover_values_of_option(ppd,
                                                             current_option_keys,
                                                             option_key)
                new_option_values.extend(new_options)
            vals['printer_option_choices'] = new_option_values

            self._cleanup_ppd(ppd_path)
        return vals

    def _load_printer_option_list(self, ppd):
        if len(self.printer_options) > 0 or not self:
            # Only fetch options the first time or
            # if the printer is already in the system.
            return
        option_inserts = []
        for option_group in ppd.optionGroups:
            for option in option_group.options:
                option_inserts.append((0, 0, {'option_key': option.keyword}))
        self.printer_options = option_inserts

    def discover_values_of_option(self, ppd, current_option_keys, option_key):
        """ Returns all new values for one printer option category. Most
        probably it will insert all option values the first time we sync with
        CUPS and then return an empty list."""
        option = ppd.findOption(option_key)
        if not option:
            return []

        printer_option_values = {entry['choice'] for entry in option.choices}
        option_model = self.env['printer.option.choice']

        # Insertion tuples
        return [
            (0, 0,
             {'option_value': option_value, 'option_key': option_key})
            for option_value in printer_option_values
            if option_model.build_composite_key(option_key, option_value)
            not in current_option_keys
        ]

    @api.multi
    def print_options(self, report=None, **print_opts):
        # Use lpoptions to have an exhaustive list of the supported options
        options = super().print_options(report=report, **print_opts)

        if report is not None:
            # Some modules pass report_name instead of the report.
            full_report = self.env['report']._get_report_from_name(report) \
                if isinstance(report, str) else report
            for printer_option in full_report.printer_options:
                options[
                    printer_option.option_key] = printer_option.option_value
        return options
