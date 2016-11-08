# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import errno
import logging
import os

from openerp import models, fields, api

_logger = logging.getLogger(__name__)

try:
    import cups
except ImportError:
    _logger.debug('Cannot `import cups`.')


class Printer(models.Model):
    _inherit = 'printing.printer'

    tray_ids = fields.One2many(comodel_name='printing.tray',
                               inverse_name='printer_id',
                               string='Paper Sources')

    @api.multi
    def _prepare_update_from_cups(self, cups_connection, cups_printer):
        vals = super(Printer, self)._prepare_update_from_cups(cups_connection,
                                                              cups_printer)

        ppd_info = cups_connection.getPPD3(self.system_name)
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
    def print_options(self, report, format, copies=1):
        """ Hook to define Tray """
        printing_act_obj = self.env['printing.report.xml.action']
        options = super(Printer, self).print_options(report, format)

        # Retrieve user default values
        user = self.env.user
        tray = user.printer_tray_id

        # Retrieve report default values
        if report.printer_tray_id:
            tray = report.printer_tray_id

        # Retrieve report-user specific values
        action = printing_act_obj.search([('report_id', '=', report.id),
                                          ('user_id', '=', self.env.uid),
                                          ('action', '!=', 'user_default')],
                                         limit=1)
        if action.printer_tray_id:
            tray = action.printer_tray_id

        if tray:
            options['InputSlot'] = str(tray.system_name)
        return options
