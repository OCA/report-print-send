# -*- coding: utf-8 -*-
# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import SUPERUSER_ID, api
from openerp.tools.config import config

__name__ = 'Create a printing.server record from previous configuration'


def migrate(cr, v):
    with api.Environment.manage():
        uid = SUPERUSER_ID
        env = api.Environment(cr, uid, {})
        env['printing.server'].create({
            'name': config.get('cups_host', 'localhost'),
            'address': config.get('cups_host', 'localhost'),
            'port': config.get('cups_port', 631),
            'printer_ids': [(6, 0, env['printing.printer'].search([]).ids)],
        })
        # Update the noupdate=1 cron if modified fields weren't touched
        cron = env.ref("base_report_to_printer.ir_cron_update_printers")
        if (
            cron.model == "printing.printer" and
            cron.function == "update_printers_status"
        ):
            cron.write({
                "function": "action_update_jobs",
                "model": "printing.server",
            })
