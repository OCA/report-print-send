# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

from . import zpl2

_logger = logging.getLogger(__name__)


DEFAULT_PYTHON_CODE = """# Python One-Liners
#  - object: %s record on which the action is triggered; may be void
#  - page_number: Current Page
#  - page_count: Total Page
#  - time, datetime: Python libraries
#  - write instead 'component_not_show' to don't show this component
#  Example: object.name


""
"""


class PrintingLabelZpl2Component(models.Model):
    _name = "printing.label.zpl2.component"
    _description = "ZPL II Label Component"
    _order = "sequence, id"

    label_id = fields.Many2one(
        comodel_name="printing.label.zpl2",
        string="Label",
        required=True,
        ondelete="cascade",
        help="Label using this component.",
    )
    sequence = fields.Integer(help="Order used to print the elements.")
    name = fields.Char(required=True, help="Name of the component.")
    origin_x = fields.Integer(
        required=True,
        default=10,
        help="Origin point of the component in the label, X coordinate.",
    )
    origin_y = fields.Integer(
        required=True,
        default=10,
        help="Origin point of the component in the label, Y coordinate.",
    )
    component_type = fields.Selection(
        selection=[
            ("text", "Text"),
            ("rectangle", "Rectangle / Line"),
            ("diagonal", "Diagonal Line"),
            ("circle", "Circle"),
            ("graphic", "Graphic"),
            (str(zpl2.BARCODE_CODE_11), "Code 11"),
            (str(zpl2.BARCODE_INTERLEAVED_2_OF_5), "Interleaved 2 of 5"),
            (str(zpl2.BARCODE_CODE_39), "Code 39"),
            (str(zpl2.BARCODE_CODE_49), "Code 49"),
            (str(zpl2.BARCODE_PDF417), "PDF417"),
            (str(zpl2.BARCODE_EAN_8), "EAN-8"),
            (str(zpl2.BARCODE_UPC_E), "UPC-E"),
            (str(zpl2.BARCODE_CODE_128), "Code 128"),
            (str(zpl2.BARCODE_EAN_13), "EAN-13"),
            (str(zpl2.BARCODE_QR_CODE), "QR Code"),
            ("sublabel", "Sublabel"),
            ("zpl2_raw", "ZPL2"),
        ],
        string="Type",
        required=True,
        default="text",
        help="Type of content, simple text or barcode.",
    )
    font = fields.Selection(
        selection=[
            (str(zpl2.FONT_DEFAULT), "Default"),
            (str(zpl2.FONT_9X5), "9x5"),
            (str(zpl2.FONT_11X7), "11x7"),
            (str(zpl2.FONT_18X10), "18x10"),
            (str(zpl2.FONT_28X15), "28x15"),
            (str(zpl2.FONT_26X13), "26x13"),
            (str(zpl2.FONT_60X40), "60x40"),
            (str(zpl2.FONT_21X13), "21x13"),
        ],
        required=True,
        default=str(zpl2.FONT_DEFAULT),
        help="Font to use, for text only.",
    )
    thickness = fields.Integer(help="Thickness of the line to draw.")
    color = fields.Selection(
        selection=[(str(zpl2.COLOR_BLACK), "Black"), (str(zpl2.COLOR_WHITE), "White")],
        default=str(zpl2.COLOR_BLACK),
        help="Color of the line to draw.",
    )
    orientation = fields.Selection(
        selection=[
            (str(zpl2.ORIENTATION_NORMAL), "Normal"),
            (str(zpl2.ORIENTATION_ROTATED), "Rotated"),
            (str(zpl2.ORIENTATION_INVERTED), "Inverted"),
            (str(zpl2.ORIENTATION_BOTTOM_UP), "Read from Bottom up"),
        ],
        required=True,
        default=str(zpl2.ORIENTATION_NORMAL),
        help="Orientation of the barcode.",
    )
    diagonal_orientation = fields.Selection(
        selection=[
            (str(zpl2.DIAGONAL_ORIENTATION_LEFT), "Left (\\)"),
            (str(zpl2.DIAGONAL_ORIENTATION_RIGHT), "Right (/)"),
        ],
        default=str(zpl2.DIAGONAL_ORIENTATION_LEFT),
        help="Orientation of the diagonal line.",
    )
    data_autofill = fields.Boolean(
        string="Autofill Data",
        help="Change 'data' with dictionary of the object information.",
    )
    check_digits = fields.Boolean(
        help="Check if you want to compute and print the check digit."
    )
    height = fields.Integer(
        help="Height of the printed component. For a text component, height "
        "of a single character."
    )
    width = fields.Integer(
        help="Width of the printed component. For a text component, width of "
        "a single character."
    )
    rounding = fields.Integer(help="Rounding of the printed rectangle corners.")
    interpretation_line = fields.Boolean(
        help="Check if you want the interpretation line to be printed."
    )
    interpretation_line_above = fields.Boolean(
        help="Check if you want the interpretation line to be printed above "
        "the barcode."
    )
    module_width = fields.Integer(default=2, help="Module width for the barcode.")
    bar_width_ratio = fields.Float(
        default=3.0, help="Ratio between wide bar and narrow bar."
    )
    security_level = fields.Integer(help="Security level for error detection.")
    columns_count = fields.Integer(help="Number of data columns to encode.")
    rows_count = fields.Integer(help="Number of rows to encode.")
    truncate = fields.Boolean(help="Check if you want to truncate the barcode.")
    model = fields.Selection(
        selection=[
            (str(zpl2.MODEL_ORIGINAL), "Original"),
            (str(zpl2.MODEL_ENHANCED), "Enhanced"),
        ],
        default=str(zpl2.MODEL_ENHANCED),
        help="Barcode model, used by some barcode types like QR Code.",
    )
    magnification_factor = fields.Integer(
        default=1, help="Magnification Factor, from 1 to 10."
    )
    only_product_barcode = fields.Boolean("Only product barcode data")
    error_correction = fields.Selection(
        selection=[
            (str(zpl2.ERROR_CORRECTION_ULTRA_HIGH), "Ultra-high Reliability Level"),
            (str(zpl2.ERROR_CORRECTION_HIGH), "High Reliability Level"),
            (str(zpl2.ERROR_CORRECTION_STANDARD), "Standard Level"),
            (str(zpl2.ERROR_CORRECTION_HIGH_DENSITY), "High Density Level"),
        ],
        required=True,
        default=str(zpl2.ERROR_CORRECTION_HIGH),
        help="Error correction for some barcode types like QR Code.",
    )
    mask_value = fields.Integer(default=7, help="Mask Value, from 0 to 7.")
    model_id = fields.Many2one(
        comodel_name="ir.model", compute="_compute_model_id", string="Record's model"
    )
    data = fields.Text(
        default=lambda self: self._compute_default_data(),
        required=True,
        help="Data to print on this component. Resource values can be "
        "inserted with %(object.field_name)s.",
    )
    sublabel_id = fields.Many2one(
        comodel_name="printing.label.zpl2",
        string="Sublabel",
        help="Another label to include into this one as a component. "
        "This allows to define reusable labels parts.",
    )
    repeat = fields.Boolean(
        string="Repeatable",
        help="Check this box to repeat this component on the label.",
    )
    repeat_offset = fields.Integer(
        default=0, help="Number of elements to skip when reading a list of elements."
    )
    repeat_count = fields.Integer(
        default=1, help="Maximum count of repeats of the component."
    )
    repeat_offset_x = fields.Integer(
        help="X coordinate offset between each occurence of this component on "
        "the label."
    )
    repeat_offset_y = fields.Integer(
        help="Y coordinate offset between each occurence of this component on "
        "the label."
    )
    reverse_print = fields.Boolean(
        help="If checked, the data will be printed in the inverse color of "
        "the background."
    )
    in_block = fields.Boolean(
        help="If checked, the data will be restrected in a "
        "defined block on the label."
    )
    block_width = fields.Integer(help="Width of the block.")
    block_lines = fields.Integer(
        default=1, help="Maximum number of lines to print in the block."
    )
    block_spaces = fields.Integer(
        help="Number of spaces added between lines in the block."
    )
    block_justify = fields.Selection(
        selection=[
            (str(zpl2.JUSTIFY_LEFT), "Left"),
            (str(zpl2.JUSTIFY_CENTER), "Center"),
            (str(zpl2.JUSTIFY_JUSTIFIED), "Justified"),
            (str(zpl2.JUSTIFY_RIGHT), "Right"),
        ],
        string="Justify",
        required=True,
        default="L",
        help="Choose how the text will be justified in the block.",
    )
    block_left_margin = fields.Integer(
        string="Left Margin",
        help="Left margin for the second and other lines in the block.",
    )
    graphic_image = fields.Binary(
        string="Image",
        attachment=True,
        help="This field holds a static image to print. "
        "If not set, the data field is evaluated.",
    )

    def process_model(self, model):
        # Used for expansions of this module
        return model

    @api.depends("label_id.model_id")
    def _compute_model_id(self):
        # it's 'compute' instead of 'related' because is easier to expand it
        for component in self:
            component.model_id = self.process_model(component.label_id.model_id)

    def _compute_default_data(self):
        model_id = self.env.context.get("default_model_id") or self.model_id.id
        model = self.env["ir.model"].browse(model_id)
        model = self.process_model(model)
        return DEFAULT_PYTHON_CODE % (model.model or "")

    @api.onchange("model_id", "data")
    def _onchange_data(self):
        for component in self.filtered(lambda c: not c.data):
            component.data = component._compute_default_data()

    @api.onchange("component_type")
    def _onchange_component_type(self):
        for component in self:
            if component.component_type == "qr_code":
                component.data_autofill = True
            else:
                component.data_autofill = False

    @api.model
    def autofill_data(self, record, eval_args):
        data = {}
        usual_fields = ["id", "create_date", record.display_name]
        for field in usual_fields:
            if hasattr(record, field):
                data[field] = getattr(record, field)
        return data

    def action_plus_origin_x(self):
        self.ensure_one()
        self.origin_x += 10

    def action_minus_origin_x(self):
        self.ensure_one()
        self.origin_x -= 10

    def action_plus_origin_y(self):
        self.ensure_one()
        self.origin_y += 10

    def action_minus_origin_y(self):
        self.ensure_one()
        self.origin_y -= 10
