# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PrintingAuto(models.Model):
    _inherit = "printing.auto"

    is_label = fields.Boolean("Is Label")

    def _get_behaviour(self):
        if self.is_label and not self.printer_id:
            return {"printer": self.env.user.default_label_printer_id}
        return super()._get_behaviour()
