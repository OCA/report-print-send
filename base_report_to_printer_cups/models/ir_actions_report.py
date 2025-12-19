# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)

REPORT_TYPES = {"qweb-pdf": "pdf", "qweb-text": "text"}


class IrActionsReportCups(models.Model):
    _inherit = "ir.actions.report"

    def behaviour(self):
        res = super().behaviour()
        printer = res.get("printer")
        if printer:
            # When no printer is available we can fallback to the default behavior
            # letting the user to manually print the reports.
            try:
                printer.server_id._open_connection(raise_on_error=True)
                printer_exception = printer.status in [
                    "error",
                    "server-error",
                    "unavailable",
                ]
            except Exception:
                printer_exception = True
            if printer_exception and not self.env.context.get("skip_printer_exception"):
                res["printer_exception"] = True
        return res
