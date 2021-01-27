##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models


class PrintingPrinterUpdateWizard(models.TransientModel):
    _inherit = "printing.printer.update.wizard"

    def action_ok(self):
        self.ensure_one()
        self.env["printing.printer"].update_print_node_printers()
        return super(PrintingPrinterUpdateWizard, self).action_ok()
