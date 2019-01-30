# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class PrintingAction(models.Model):
    _name = 'printing.action'
    _description = 'Print Job Action'

    @api.model
    def _available_action_types(self):
        return [
            ('server', 'Send to Printer'),
            ('client', 'Send to Client'),
            ('user_default', "Use user's defaults"),
        ]

    name = fields.Char(required=True)
    action_type = fields.Selection(
        selection=_available_action_types,
        string='Type',
        required=True,
        oldname='type'
    )
