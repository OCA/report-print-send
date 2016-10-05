# -*- coding: utf-8 -*-
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp.exceptions import UserError
from openerp import models, api, _

from ..models.printing_printer import CUPS_HOST, CUPS_PORT

try:
    import cups
except ImportError:
    _logger = logging.getLogger(__name__)
    _logger.debug('Cannot `import cups`.')


_logger = logging.getLogger(__name__)


class PrintingPrinterUpdateWizard(models.TransientModel):
    _name = 'printing.printer.update.wizard'
    _description = 'Printing Printer Update Wizard'

    @api.model
    def action_ok(self):
        # Update Printers
        printer_obj = self.env['printing.printer']
        try:
            _logger.info('Trying to get list of printers')
            connection = cups.Connection(CUPS_HOST, CUPS_PORT)
            printers = connection.getPrinters()
            _logger.info('Printers found: %s' % ','.join(printers.keys()))
        except:
            raise UserError(
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
            printer_obj.create(values)
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
