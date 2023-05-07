from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    print_config_id = fields.Many2one(comodel_name="print.config")
