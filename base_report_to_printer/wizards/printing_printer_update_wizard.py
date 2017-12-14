# -*- coding: utf-8 -*-
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, api


_logger = logging.getLogger(__name__)


class PrintingPrinterUpdateWizard(models.TransientModel):
    _name = 'printing.printer.update.wizard'
    _description = 'Printing Printer Update Wizard'

    @api.multi
    def action_ok(self):
        self.env['printing.server'].search([]) \
            .update_printers(raise_on_error=True)

        return {
            'name': 'Printers',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'printing.printer',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
