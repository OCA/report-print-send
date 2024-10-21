# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .printing_action import AVAILABLE_ACTION_TYPES

action_types = [type for type in AVAILABLE_ACTION_TYPES if type[0] != "user_default"]


class ResUsers(models.Model):
    _inherit = "res.users"

    printing_action = fields.Selection(selection=action_types)
    printing_printer_id = fields.Many2one(
        comodel_name="printing.printer", string="Default Printer"
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["printing_action", "printing_printer_id"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + [
            "printing_action",
            "printing_printer_id",
        ]

    printer_tray_id = fields.Many2one(
        comodel_name="printing.tray",
        string="Default Printer Paper Source",
        domain="[('printer_id', '=', printing_printer_id)]",
    )

    @api.onchange("printing_printer_id")
    def onchange_printing_printer_id(self):
        """Reset the tray when the printer is changed"""
        self.printer_tray_id = False
