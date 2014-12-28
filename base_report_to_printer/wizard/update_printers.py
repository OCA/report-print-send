# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2014 Camptocamp SA (<http://www.camptocamp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import cups
from openerp.exceptions import Warning
from openerp import models, api, _
from openerp.tools.config import config
import logging

_logger = logging.getLogger(__name__)
CUPS_HOST = config.get('cups_host', 'localhost')
CUPS_PORT = int(config.get('cups_port', 631))


class PrintingPrinterUpdateWizard(models.TransientModel):
    _name = 'printing.printer.update.wizard'

    @api.multi
    def action_ok(self):
        self.ensure_one()
        # Update Printers
        printer_obj = self.env['printing.printer']
        try:
            _logger.info('Trying to get list of printers')
            connection = cups.Connection(CUPS_HOST, CUPS_PORT)
            printers = connection.getPrinters()
            _logger.info('Printers found: %s' % ','.join(printers.keys()))
        except:
            raise Warning(
                _('Could not get the list of printers from the CUPS server '
                    '(%s:%s)') % (CUPS_HOST, CUPS_PORT))

        printer_recs = printer_obj.search(
            [('system_name', 'in', printers.keys())]
        )
        for printer in printer_recs:
            del printers[printer.system_name]
            _logger.info(
                'Printer %s was already created' % printer.system_name)

        for name, printer in printers.iteritems():
            values = {
                'name': printer['printer-info'],
                'system_name': name,
                'model': printer.get('printer-make-and-model', False),
                'location': printer.get('printer-location', False),
                'uri': printer.get('device-uri', False),
            }
            self.env['printing.printer'].create(values)
            _logger.info(
                'Created new printer %s with URI %s'
                % (values['name'], values['uri']))

        return {
            'name': 'Printers',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'printing.printer',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
