# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
import logging

from PIL import Image, ImageOps

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

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
            (str(zpl2.BARCODE_GS1_128), "GS1-128"),
            ("sublabel", "Sublabel"),
            ("zpl2_raw", "ZPL2"),
        ],
        string="Type",
        required=True,
        default="text",
        help="Type of content, simple text or barcode.",
    )

    gs1_ai_ids = fields.One2many(
        "printing.label.zpl2.gs1.ai",
        "component_id",
        string="GS1 Application Identifiers",
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

    def _get_data(self, record, eval_args):
        if self.data_autofill:
            return self.autofill_data(record, eval_args)
        data = safe_eval(str(self.data), eval_args) or ""
        if hasattr(self, "_postprocess_data_%s" % self.component_type):
            data = getattr(self, "_postprocess_data_%s" % self.component_type)(
                data, record, eval_args
            )
        return data

    def _postprocess_data_gs1_128(self, data, record, eval_args):
        return self._generate_gs1_128_data(record)

    def _postprocess_data_qr_code(self, data, record, eval_args):
        return "{}A,{}".format(self.error_correction, data)

    @api.model
    def autofill_data(self, record, eval_args):
        data = {}
        usual_fields = ["id", "create_date", record.display_name]
        for field in usual_fields:
            if hasattr(record, field):
                data[field] = getattr(record, field)
        return data

    def _generate_gs1_128_data(self, record):
        data = []
        for ai_config in self.gs1_ai_ids:
            ai, value = ai_config._format_gs1_value(record)
            if value:
                data.append(f"({ai}){value}")
        return ">8".join(data) if data else "component_not_show"

    def _process_type_text(self, label_data, data, offset_x, offset_y, record):
        component_offset_x = self.origin_x + offset_x
        component_offset_y = self.origin_y + offset_y
        format_arguments = {
            field_name: self[field_name]
            for field_name in [
                zpl2.ARG_FONT,
                zpl2.ARG_ORIENTATION,
                zpl2.ARG_HEIGHT,
                zpl2.ARG_WIDTH,
                zpl2.ARG_REVERSE_PRINT,
                zpl2.ARG_IN_BLOCK,
                zpl2.ARG_BLOCK_WIDTH,
                zpl2.ARG_BLOCK_LINES,
                zpl2.ARG_BLOCK_SPACES,
                zpl2.ARG_BLOCK_JUSTIFY,
                zpl2.ARG_BLOCK_LEFT_MARGIN,
            ]
        }
        label_data.font_data(
            component_offset_x, component_offset_y, format_arguments, data
        )

    def _process_type_zpl2_raw(self, label_data, data, *args):
        label_data._write_command(data)

    def _process_type_rectangle(self, label_data, data, offset_x, offset_y, record):
        label_data.graphic_box(
            self.origin_x + offset_x,
            self.origin_y + offset_y,
            {
                zpl2.ARG_WIDTH: self.width,
                zpl2.ARG_HEIGHT: self.height,
                zpl2.ARG_THICKNESS: self.thickness,
                zpl2.ARG_COLOR: self.color,
                zpl2.ARG_ROUNDING: self.rounding,
            },
        )

    def _process_type_diagonal(self, label_data, data, offset_x, offset_y, record):
        label_data.graphic_diagonal_line(
            self.origin_x + offset_x,
            self.origin_y + offset_y,
            {
                zpl2.ARG_WIDTH: self.width,
                zpl2.ARG_HEIGHT: self.height,
                zpl2.ARG_THICKNESS: self.thickness,
                zpl2.ARG_COLOR: self.color,
                zpl2.ARG_DIAGONAL_ORIENTATION: self.diagonal_orientation,
            },
        )

    def _process_type_graphic(self, label_data, data, offset_x, offset_y, record):
        image = self.with_context(bin_size_graphic_image=False).graphic_image or data
        try:
            pil_image = Image.open(io.BytesIO(base64.b64decode(image))).convert("RGB")
        except Exception as e:
            _logger.warning(
                "Failed to process graphic component %s for record %s: %s",
                self.name,
                record.display_name,
                str(e),
            )
            return
        if self.width and self.height:
            pil_image = pil_image.resize((self.width, self.height))

        # Invert the colors
        if self.reverse_print:
            pil_image = ImageOps.invert(pil_image)

        # Rotation (PIL rotates counter clockwise)
        if self.orientation == zpl2.ORIENTATION_ROTATED:
            pil_image = pil_image.transpose(Image.ROTATE_270)
        elif self.orientation == zpl2.ORIENTATION_INVERTED:
            pil_image = pil_image.transpose(Image.ROTATE_180)
        elif self.orientation == zpl2.ORIENTATION_BOTTOM_UP:
            pil_image = pil_image.transpose(Image.ROTATE_90)

        label_data.graphic_field(
            self.origin_x + offset_x, self.origin_y + offset_y, pil_image
        )

    def _process_type_circle(self, label_data, data, offset_x, offset_y, record):
        label_data.graphic_circle(
            self.origin_x + offset_x,
            self.origin_y + offset_y,
            {
                zpl2.ARG_DIAMETER: self.width,
                zpl2.ARG_THICKNESS: self.thickness,
                zpl2.ARG_COLOR: self.color,
            },
        )

    def _process_type_sublabel(self, label_data, data, offset_x, offset_y, record):
        component_offset_x = self.origin_x + offset_x + self.sublabel_id.origin_x
        component_offset_y = self.origin_y + offset_y + self.sublabel_id.origin_y
        self.sublabel_id._generate_zpl2_components_data(
            label_data,
            data if isinstance(data, models.BaseModel) else record,
            label_offset_x=component_offset_x,
            label_offset_y=component_offset_y,
        )

    def _process_type_barcode(self, label_data, data, offset_x, offset_y, record):
        barcode_arguments = {
            field_name: self[field_name]
            for field_name in [
                zpl2.ARG_ORIENTATION,
                zpl2.ARG_CHECK_DIGITS,
                zpl2.ARG_HEIGHT,
                zpl2.ARG_INTERPRETATION_LINE,
                zpl2.ARG_INTERPRETATION_LINE_ABOVE,
                zpl2.ARG_SECURITY_LEVEL,
                zpl2.ARG_COLUMNS_COUNT,
                zpl2.ARG_ROWS_COUNT,
                zpl2.ARG_TRUNCATE,
                zpl2.ARG_MODULE_WIDTH,
                zpl2.ARG_BAR_WIDTH_RATIO,
                zpl2.ARG_MODEL,
                zpl2.ARG_MAGNIFICATION_FACTOR,
                zpl2.ARG_ERROR_CORRECTION,
                zpl2.ARG_MASK_VALUE,
            ]
        }
        label_data.barcode_data(
            self.origin_x + offset_x,
            self.origin_y + offset_y,
            self.component_type,
            barcode_arguments,
            data,
        )

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
