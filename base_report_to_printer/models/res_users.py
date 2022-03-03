# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _user_available_action_types(self):
        return [
            (code, string)
            for code, string in self.env["printing.action"]._available_action_types()
            if code != "user_default"
        ]

    printing_action = fields.Selection(selection=_user_available_action_types)
    printing_printer_id = fields.Many2one(
        comodel_name="printing.printer", string="Default Printer"
    )

    @api.model
    def _register_hook(self):
        super()._register_hook()
        self.SELF_WRITEABLE_FIELDS.extend(["printing_action", "printing_printer_id"])
        self.SELF_READABLE_FIELDS.extend(["printing_action", "printing_printer_id"])

    printer_tray_id = fields.Many2one(
        comodel_name="printing.tray",
        string="Default Printer Paper Source",
        domain="[('printer_id', '=', printing_printer_id)]",
    )

    @api.onchange("printing_printer_id")
    def onchange_printing_printer_id(self):
        """Reset the tray when the printer is changed"""
        self.printer_tray_id = False
