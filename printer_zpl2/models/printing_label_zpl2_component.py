# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)

try:
    import zpl2
except ImportError:
    _logger.debug('Cannot `import zpl2`.')

DEFAULT_PYTHON_CODE = """# Python One-Liners
#  - object: record on which the action is triggered; may be be void
#  - page_number: Current Page
#  - page_count: Total Page
#  - time, datetime: Python libraries
#  Exemple : object.name

""
"""


class PrintingLabelZpl2Component(models.Model):
    _name = 'printing.label.zpl2.component'
    _description = 'ZPL II Label Component'
    _order = 'sequence, id'

    label_id = fields.Many2one(
        comodel_name='printing.label.zpl2', string='Label',
        required=True, ondelete='cascade', help='Label using this component.')
    sequence = fields.Integer(help='Order used to print the elements.')
    name = fields.Char(required=True, help='Name of the component.')
    origin_x = fields.Integer(
        required=True, default=10,
        help='Origin point of the component in the label, X coordinate.')
    origin_y = fields.Integer(
        required=True, default=10,
        help='Origin point of the component in the label, Y coordinate.')
    component_type = fields.Selection(
        selection=[
            ('text', 'Text'),
            ('rectangle', 'Rectangle / Line'),
            ('diagonal', 'Diagonal Line'),
            ('circle', 'Circle'),
            ('graphic', 'Graphic'),
            (zpl2.BARCODE_CODE_11, 'Code 11'),
            (zpl2.BARCODE_INTERLEAVED_2_OF_5, 'Interleaved 2 of 5'),
            (zpl2.BARCODE_CODE_39, 'Code 39'),
            (zpl2.BARCODE_CODE_49, 'Code 49'),
            (zpl2.BARCODE_PDF417, 'PDF417'),
            (zpl2.BARCODE_EAN_8, 'EAN-8'),
            (zpl2.BARCODE_UPC_E, 'UPC-E'),
            (zpl2.BARCODE_CODE_128, 'Code 128'),
            (zpl2.BARCODE_EAN_13, 'EAN-13'),
            (zpl2.BARCODE_QR_CODE, 'QR Code'),
            ('sublabel', 'Sublabel'),
            ('zpl2_raw', 'ZPL2'),
        ], string='Type', required=True, default='text', oldname='type',
        help='Type of content, simple text or barcode.')
    font = fields.Selection(
        selection=[
            (zpl2.FONT_DEFAULT, 'Default'),
            (zpl2.FONT_9X5, '9x5'),
            (zpl2.FONT_11X7, '11x7'),
            (zpl2.FONT_18X10, '18x10'),
            (zpl2.FONT_28X15, '28x15'),
            (zpl2.FONT_26X13, '26x13'),
            (zpl2.FONT_60X40, '60x40'),
            (zpl2.FONT_21X13, '21x13'),
        ], required=True, default=zpl2.FONT_DEFAULT,
        help='Font to use, for text only.')
    thickness = fields.Integer(help='Thickness of the line to draw.')
    color = fields.Selection(
        selection=[
            (zpl2.COLOR_BLACK, 'Black'),
            (zpl2.COLOR_WHITE, 'White'),
        ], default=zpl2.COLOR_BLACK,
        help='Color of the line to draw.')
    orientation = fields.Selection(
        selection=[
            (zpl2.ORIENTATION_NORMAL, 'Normal'),
            (zpl2.ORIENTATION_ROTATED, 'Rotated'),
            (zpl2.ORIENTATION_INVERTED, 'Inverted'),
            (zpl2.ORIENTATION_BOTTOM_UP, 'Read from Bottom up'),
        ], required=True, default=zpl2.ORIENTATION_NORMAL,
        help='Orientation of the barcode.')
    diagonal_orientation = fields.Selection(
        selection=[
            (zpl2.DIAGONAL_ORIENTATION_LEFT, 'Left (\\)'),
            (zpl2.DIAGONAL_ORIENTATION_RIGHT, 'Right (/)'),
        ], default=zpl2.DIAGONAL_ORIENTATION_LEFT,
        help='Orientation of the diagonal line.')
    check_digits = fields.Boolean(
        help='Check if you want to compute and print the check digit.')
    height = fields.Integer(
        help='Height of the printed component. For a text component, height '
        'of a single character.')
    width = fields.Integer(
        help='Width of the printed component. For a text component, width of '
        'a single character.')
    rounding = fields.Integer(
        help='Rounding of the printed rectangle corners.')
    interpretation_line = fields.Boolean(
        help='Check if you want the interpretation line to be printed.')
    interpretation_line_above = fields.Boolean(
        help='Check if you want the interpretation line to be printed above '
        'the barcode.')
    module_width = fields.Integer(
        default=2, help='Module width for the barcode.')
    bar_width_ratio = fields.Float(
        default=3.0, help='Ratio between wide bar and narrow bar.')
    security_level = fields.Integer(help='Security level for error detection.')
    columns_count = fields.Integer(help='Number of data columns to encode.')
    rows_count = fields.Integer(help='Number of rows to encode.')
    truncate = fields.Boolean(
        help='Check if you want to truncate the barcode.')
    model = fields.Selection(
        selection=[
            (zpl2.MODEL_ORIGINAL, 'Original'),
            (zpl2.MODEL_ENHANCED, 'Enhanced'),
        ], default=zpl2.MODEL_ENHANCED,
        help='Barcode model, used by some barcode types like QR Code.')
    magnification_factor = fields.Integer(
        default=1, help='Magnification Factor, from 1 to 10.')
    error_correction = fields.Selection(
        selection=[
            (zpl2.ERROR_CORRECTION_ULTRA_HIGH, 'Ultra-high Reliability Level'),
            (zpl2.ERROR_CORRECTION_HIGH, 'High Reliability Level'),
            (zpl2.ERROR_CORRECTION_STANDARD, 'Standard Level'),
            (zpl2.ERROR_CORRECTION_HIGH_DENSITY, 'High Density Level'),
        ], required=True, default=zpl2.ERROR_CORRECTION_HIGH,
        help='Error correction for some barcode types like QR Code.')
    mask_value = fields.Integer(default=7, help='Mask Value, from 0 to 7.')
    data = fields.Text(
        default=DEFAULT_PYTHON_CODE, required=True,
        help='Data to print on this component. Resource values can be '
        'inserted with %(object.field_name)s.')
    sublabel_id = fields.Many2one(
        comodel_name='printing.label.zpl2', string='Sublabel',
        help='Another label to include into this one as a component. '
        'This allows to define reusable labels parts.')
    repeat = fields.Boolean(
        string='Repeatable',
        help='Check this box to repeat this component on the label.')
    repeat_offset = fields.Integer(
        default=0,
        help='Number of elements to skip when reading a list of elements.')
    repeat_count = fields.Integer(
        default=1,
        help='Maximum count of repeats of the component.')
    repeat_offset_x = fields.Integer(
        help='X coordinate offset between each occurence of this component on '
        'the label.')
    repeat_offset_y = fields.Integer(
        help='Y coordinate offset between each occurence of this component on '
        'the label.')
    reverse_print = fields.Boolean(
        help='If checked, the data will be printed in the inverse color of '
        'the background.')
    in_block = fields.Boolean(
        help='If checked, the data will be restrected in a '
        'defined block on the label.')
    block_width = fields.Integer(help='Width of the block.')
    block_lines = fields.Integer(
        default=1, help='Maximum number of lines to print in the block.')
    block_spaces = fields.Integer(
        help='Number of spaces added between lines in the block.')
    block_justify = fields.Selection(
        selection=[
            (zpl2.JUSTIFY_LEFT, 'Left'),
            (zpl2.JUSTIFY_CENTER, 'Center'),
            (zpl2.JUSTIFY_JUSTIFIED, 'Justified'),
            (zpl2.JUSTIFY_RIGHT, 'Right'),
        ], string='Justify', required=True, default='L',
        help='Choose how the text will be justified in the block.')
    block_left_margin = fields.Integer(
        string='Left Margin',
        help='Left margin for the second and other lines in the block.')
    graphic_image = fields.Binary(
        string='Image', attachment=True,
        help='This field holds a static image to print. '
             'If not set, the data field is evaluated.')
