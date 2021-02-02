##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    print_node_api_key = fields.Char(
        string="Print Node Api Key",
        config_parameter="base_report_to_print_node.api_key",
    )

    def check_api_key(self):
        raise UserError(self.env["printing_printer"]._get_response("noop"))
