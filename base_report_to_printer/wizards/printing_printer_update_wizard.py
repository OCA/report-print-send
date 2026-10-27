# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class PrintingPrinterUpdateWizard(models.TransientModel):
    _name = "printing.printer.update.wizard"
    _description = "Printing Printer Update Wizard"

    def action_ok(self):
        cnt = self.env["printing.server"].search_count([])
        self.env["printing.server"].search([], limit=cnt).update_printers(
            raise_on_error=True
        )

        return {
            "name": "Printers",
            "view_mode": "list,form",
            "res_model": "printing.printer",
            "type": "ir.actions.act_window",
            "target": "current",
        }
