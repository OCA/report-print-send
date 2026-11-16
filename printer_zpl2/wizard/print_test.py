# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class WizardZpl2PrintTest(models.TransientModel):
    _name = "wizard.zpl2.print_test"
    _description = "Print a test label"

    label_id = fields.Many2one(
        comodel_name="printing.label.zpl2", string="Label", required=True, readonly=True
    )
    model_id = fields.Many2one(related="label_id.model_id")
    record_ref = fields.Reference(
        selection="_selection_record_ref",
        string="Record",
        compute="_compute_record_ref",
        store=True,
        precompute=True,
        readonly=False,
        required=True,
        help="Record the test label is printed for.",
    )
    printer_id = fields.Many2one(
        comodel_name="printing.printer",
        string="Printer",
        required=True,
        default=lambda self: self.env["printing.printer"].get_default(),
    )
    extra = fields.Text(
        compute="_compute_extra",
        store=True,
        precompute=True,
        readonly=False,
        help="Python dictionary of extra arguments for the label expressions, "
        "the ones of the label by default.",
    )

    @api.model
    def _selection_record_ref(self):
        # The model is the one of the label, the view hides this selection
        return [
            (model.model, model.name)
            for model in self.env["ir.model"].sudo().search([])
        ]

    @api.depends("label_id")
    def _compute_record_ref(self):
        for wizard in self:
            wizard.record_ref = False
            model = wizard.label_id.model_id.model
            if model:
                # The most recent record of the model
                record = self.env[model].search([], limit=1, order="id desc")
                if record:
                    wizard.record_ref = f"{model},{record.id}"

    @api.depends("label_id")
    def _compute_extra(self):
        for wizard in self:
            wizard.extra = wizard.label_id.extra

    def action_print(self):
        self.ensure_one()
        if self.record_ref._name != self.label_id.model_id.model:
            raise UserError(
                self.env._("The record must be a %s.", self.label_id.model_id.name)
            )
        extra = safe_eval(self.extra or "{}", {"env": self.env})
        self.label_id.print_label(self.printer_id, self.record_ref, **extra)
