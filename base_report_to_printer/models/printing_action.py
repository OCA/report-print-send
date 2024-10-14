# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

AVAILABLE_ACTION_TYPES = [
    ("server", "Send to Printer"),
    ("client", "Send to Client"),
    ("user_default", "Use user's defaults"),
]


class PrintingAction(models.Model):
    _name = "printing.action"
    _description = "Print Job Action"

    _available_action_types = AVAILABLE_ACTION_TYPES

    name = fields.Char(required=True)
    action_type = fields.Selection(
        selection=AVAILABLE_ACTION_TYPES, string="Type", required=True
    )
