# Copyright (C) 2019 IBM Corp.
# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    is_default_report = fields.Boolean("Is Default Report?")
    country_id = fields.Many2one("res.country", string="Country")
    company_id = fields.Many2one("res.company", string="Company")
