# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Copied from https://github.com/subteno-it/python-zpl2, as there has been new releases
# that breaks current code without clear source (no commit on the repo). As the amount
# of code is not too much, we put it on the module itself, being able to control the
# whole chain, and to reduce the code with the considerations of current Odoo version

import binascii
import math

from PIL import ImageOps

# Constants for the printer configuration management
CONF_RELOAD_FACTORY = "F"
CONF_RELOAD_NETWORK_FACTORY = "N"
CONF_RECALL_LAST_SAVED = "R"
CONF_SAVE_CURRENT = "S"

# Command arguments names
ARG_FONT = "font"
ARG_HEIGHT = "height"
ARG_WIDTH = "width"
ARG_ORIENTATION = "orientation"
ARG_THICKNESS = "thickness"
ARG_BLOCK_WIDTH = "block_width"
ARG_BLOCK_LINES = "block_lines"
ARG_BLOCK_SPACES = "block_spaces"
ARG_BLOCK_JUSTIFY = "block_justify"
ARG_BLOCK_LEFT_MARGIN = "block_left_margin"
ARG_CHECK_DIGITS = "check_digits"
ARG_INTERPRETATION_LINE = "interpretation_line"
ARG_INTERPRETATION_LINE_ABOVE = "interpretation_line_above"
ARG_STARTING_MODE = "starting_mode"
ARG_SECURITY_LEVEL = "security_level"
ARG_COLUMNS_COUNT = "columns_count"
ARG_ROWS_COUNT = "rows_count"
ARG_TRUNCATE = "truncate"
ARG_MODE = "mode"
ARG_MODULE_WIDTH = "module_width"
ARG_BAR_WIDTH_RATIO = "bar_width_ratio"
ARG_REVERSE_PRINT = "reverse_print"
ARG_IN_BLOCK = "in_block"
ARG_COLOR = "color"
ARG_ROUNDING = "rounding"
ARG_DIAMETER = "diameter"
ARG_DIAGONAL_ORIENTATION = "diagonal_orientation"
ARG_MODEL = "model"
ARG_MAGNIFICATION_FACTOR = "magnification_factor"
ARG_ERROR_CORRECTION = "error_correction"
ARG_MASK_VALUE = "mask_value"

# Model values
MODEL_ORIGINAL = 1
MODEL_ENHANCED = 2

# Error Correction
ERROR_CORRECTION_ULTRA_HIGH = "H"
ERROR_CORRECTION_HIGH = "Q"
ERROR_CORRECTION_STANDARD = "M"
ERROR_CORRECTION_HIGH_DENSITY = "L"

# Boolean values
BOOL_YES = "Y"
BOOL_NO = "N"

# Orientation values
ORIENTATION_NORMAL = "N"
ORIENTATION_ROTATED = "R"
ORIENTATION_INVERTED = "I"
ORIENTATION_BOTTOM_UP = "B"

# Diagonal lines orientation values
DIAGONAL_ORIENTATION_LEFT = "L"
DIAGONAL_ORIENTATION_RIGHT = "R"

# Justify values
JUSTIFY_LEFT = "L"
JUSTIFY_CENTER = "C"
JUSTIFY_JUSTIFIED = "J"
JUSTIFY_RIGHT = "R"

# Font values
FONT_DEFAULT = "0"
FONT_9X5 = "A"
FONT_11X7 = "B"
FONT_18X10 = "D"
FONT_28X15 = "E"
FONT_26X13 = "F"
FONT_60X40 = "G"
FONT_21X13 = "H"

# Color values
COLOR_BLACK = "B"
COLOR_WHITE = "W"

# Barcode types
BARCODE_CODE_11 = "code_11"
BARCODE_INTERLEAVED_2_OF_5 = "interleaved_2_of_5"
BARCODE_CODE_39 = "code_39"
BARCODE_CODE_49 = "code_49"
BARCODE_PDF417 = "pdf417"
BARCODE_EAN_8 = "ean-8"
BARCODE_UPC_E = "upc-e"
BARCODE_CODE_128 = "code_128"
BARCODE_EAN_13 = "ean-13"
BARCODE_QR_CODE = "qr_code"


class Zpl2(object):
    """ZPL II management class
    Allows to generate data for Zebra printers
    """

    def __init__(self):
        self.encoding = "utf-8"
        self.initialize()

    def initialize(self):
        self._buffer = []

    def output(self):
        """Return the full contents to send to the printer"""
        return "\n".encode(self.encoding).join(self._buffer)

    def _enforce(self, value, minimum=1, maximum=32000):
        """Returns the value, forced between minimum and maximum"""
        return min(max(minimum, value), maximum)

    def _write_command(self, data):
        """Adds a complete command to buffer"""
        self._buffer.append(str(data).encode(self.encoding))

    def _generate_arguments(self, arguments, kwargs):
        """Generate a zebra arguments from an argument names list and a dict of
        values for these arguments
        @param arguments : list of argument names, ORDER MATTERS
        @param kwargs : list of arguments values
        """
        command_arguments = []
        # Add all arguments in the list, if they exist
        for argument in arguments:
            if kwargs.get(argument, None) is not None:
                if isinstance(kwargs[argument], bool):
                    kwargs[argument] = kwargs[argument] and BOOL_YES or BOOL_NO
                command_arguments.append(kwargs[argument])

        # Return a zebra formatted string, with a comma between each argument
        return ",".join(map(str, command_arguments))

    def print_width(self, label_width):
        """Defines the print width setting on the printer"""
        self._write_command("^PW%d" % label_width)

    def configuration_update(self, active_configuration):
        """Set the active configuration on the printer"""
        self._write_command("^JU%s" % active_configuration)

    def label_start(self):
        """Adds the label start command to the buffer"""
        self._write_command("^XA")

    def label_encoding(self):
        """Adds the label encoding command to the buffer
        Fixed value defined to UTF-8
        """
        self._write_command("^CI28")

    def label_end(self):
        """Adds the label start command to the buffer"""
        self._write_command("^XZ")

    def label_home(self, left, top):
        """Define the label top left corner"""
        self._write_command("^LH%d,%d" % (left, top))

    def _field_origin(self, right, down):
        """Define the top left corner of the data, from the top left corner of
        the label
        """
        return "^FO%d,%d" % (right, down)

    def _font_format(self, font_format):
        """Send the commands which define the font to use for the current data"""
        arguments = [ARG_FONT, ARG_HEIGHT, ARG_WIDTH]
        # Add orientation in the font name (only place where there is
        # no comma between values)
        font_format[ARG_FONT] += font_format.get(ARG_ORIENTATION, ORIENTATION_NORMAL)
        # Check that the height value fits in the allowed values
        if font_format.get(ARG_HEIGHT) is not None:
            font_format[ARG_HEIGHT] = self._enforce(font_format[ARG_HEIGHT], minimum=10)
        # Check that the width value fits in the allowed values
        if font_format.get(ARG_WIDTH) is not None:
            font_format[ARG_WIDTH] = self._enforce(font_format[ARG_WIDTH], minimum=10)
        # Generate the ZPL II command
        return "^A" + self._generate_arguments(arguments, font_format)

    def _field_block(self, block_format):
        """Define a maximum width to print some data"""
        arguments = [
            ARG_BLOCK_WIDTH,
            ARG_BLOCK_LINES,
            ARG_BLOCK_SPACES,
            ARG_BLOCK_JUSTIFY,
            ARG_BLOCK_LEFT_MARGIN,
        ]
        return "^FB" + self._generate_arguments(arguments, block_format)

    def _barcode_format(self, barcodeType, barcode_format):
        """Generate the commands to print a barcode
        Each barcode type needs a specific function
        """

        def _code11(**kwargs):
            arguments = [
                ARG_ORIENTATION,
                ARG_CHECK_DIGITS,
                ARG_HEIGHT,
                ARG_INTERPRETATION_LINE,
                ARG_INTERPRETATION_LINE_ABOVE,
            ]
            return "1" + self._generate_arguments(arguments, kwargs)

        def _interleaved2of5(**kwargs):
            arguments = [
                ARG_ORIENTATION,
                ARG_HEIGHT,
                ARG_INTERPRETATION_LINE,
                ARG_INTERPRETATION_LINE_ABOVE,
                ARG_CHECK_DIGITS,
            ]
            return "2" + self._generate_arguments(arguments, kwargs)

        def _code39(**kwargs):
            arguments = [
                ARG_ORIENTATION,
                ARG_CHECK_DIGITS,
                ARG_HEIGHT,
                ARG_INTERPRETATION_LINE,
                ARG_INTERPRETATION_LINE_ABOVE,
            ]
            return "3" + self._generate_arguments(arguments, kwargs)

        def _code49(**kwargs):
            arguments = [
                ARG_ORIENTATION,
                ARG_HEIGHT,
                ARG_INTERPRETATION_LINE,
                ARG_STARTING_MODE,
            ]
            # Use interpretation_line and interpretation_line_above to generate
            # a specific interpretation_line value
            if kwargs.get(ARG_INTERPRETATION_LINE) is not None:
                if kwargs[ARG_INTERPRETATION_LINE]:
                    if kwargs[ARG_INTERPRETATION_LINE_ABOVE]:
                        # Interpretation line after
                        kwargs[ARG_INTERPRETATION_LINE] = "A"
                    else:
                        # Interpretation line before
                        kwargs[ARG_INTERPRETATION_LINE] = "B"
                else:
                    # No interpretation line
                    kwargs[ARG_INTERPRETATION_LINE] = "N"
            return "4" + self._generate_arguments(arguments, kwargs)

        def _pdf417(**kwargs):
            arguments = [
                ARG_ORIENTATION,
                ARG_HEIGHT,
                ARG_SECURITY_LEVEL,
                ARG_COLUMNS_COUNT,
                ARG_ROWS_COUNT,
                ARG_TRUNCATE,
            ]
            return "7" + self._generate_arguments(arguments, kwargs)

        def _ean8(**kwargs):
            arguments = [
                ARG_ORIENTATION,
                ARG_HEIGHT,
                ARG_INTERPRETATION_LINE,
                ARG_INTERPRETATION_LINE_ABOVE,
            ]
            return "8" + self._generate_arguments(arguments, kwargs)

        def _upce(**kwargs):
            arguments = [
                ARG_ORIENTATION,
                ARG_HEIGHT,
                ARG_INTERPRETATION_LINE,
                ARG_INTERPRETATION_LINE_ABOVE,
                ARG_CHECK_DIGITS,
            ]
            return "9" + self._generate_arguments(arguments, kwargs)

        def _code128(**kwargs):
            arguments = [
                ARG_ORIENTATION,
                ARG_HEIGHT,
                ARG_INTERPRETATION_LINE,
                ARG_INTERPRETATION_LINE_ABOVE,
                ARG_CHECK_DIGITS,
                ARG_MODE,
            ]
            return "C" + self._generate_arguments(arguments, kwargs)

        def _ean13(**kwargs):
            arguments = [
                ARG_ORIENTATION,
                ARG_HEIGHT,
                ARG_INTERPRETATION_LINE,
                ARG_INTERPRETATION_LINE_ABOVE,
            ]
            return "E" + self._generate_arguments(arguments, kwargs)

        def _qrcode(**kwargs):
            arguments = [
                ARG_ORIENTATION,
                ARG_MODEL,
                ARG_MAGNIFICATION_FACTOR,
                ARG_ERROR_CORRECTION,
                ARG_MASK_VALUE,
            ]
            return "Q" + self._generate_arguments(arguments, kwargs)

        barcodeTypes = {
            BARCODE_CODE_11: _code11,
            BARCODE_INTERLEAVED_2_OF_5: _interleaved2of5,
            BARCODE_CODE_39: _code39,
            BARCODE_CODE_49: _code49,
            BARCODE_PDF417: _pdf417,
            BARCODE_EAN_8: _ean8,
            BARCODE_UPC_E: _upce,
            BARCODE_CODE_128: _code128,
            BARCODE_EAN_13: _ean13,
            BARCODE_QR_CODE: _qrcode,
        }
        return "^B" + barcodeTypes[barcodeType](**barcode_format)

    def _barcode_field_default(self, barcode_format):
        """Add the data start command to the buffer"""
        arguments = [
            ARG_MODULE_WIDTH,
            ARG_BAR_WIDTH_RATIO,
        ]
        return "^BY" + self._generate_arguments(arguments, barcode_format)

    def _field_data_start(self):
        """Add the data start command to the buffer"""
        return "^FD"

    def _field_reverse_print(self):
        """Allows the printed data to appear white over black, or black over white"""
        return "^FR"

    def _field_data_stop(self):
        """Add the data stop command to the buffer"""
        return "^FS"

    def _field_data(self, data):
        """Add data to the buffer, between start and stop commands"""
        command = "{start}{data}{stop}".format(
            start=self._field_data_start(),
            data=data,
            stop=self._field_data_stop(),
        )
        return command

    def font_data(self, right, down, field_format, data):
        """Add a full text in the buffer, with needed formatting commands"""
        reverse = ""
        if field_format.get(ARG_REVERSE_PRINT, False):
            reverse = self._field_reverse_print()
        block = ""
        if field_format.get(ARG_IN_BLOCK, False):
            block = self._field_block(field_format)
        command = "{origin}{font_format}{reverse}{block}{data}".format(
            origin=self._field_origin(right, down),
            font_format=self._font_format(field_format),
            reverse=reverse,
            block=block,
            data=self._field_data(data),
        )
        self._write_command(command)

    def barcode_data(self, right, down, barcodeType, barcode_format, data):
        """Add a full barcode in the buffer, with needed formatting commands"""
        command = "{default}{origin}{barcode_format}{data}".format(
            default=self._barcode_field_default(barcode_format),
            origin=self._field_origin(right, down),
            barcode_format=self._barcode_format(barcodeType, barcode_format),
            data=self._field_data(data),
        )
        self._write_command(command)

    def graphic_box(self, right, down, graphic_format):
        """Send the commands to draw a rectangle"""
        arguments = [
            ARG_WIDTH,
            ARG_HEIGHT,
            ARG_THICKNESS,
            ARG_COLOR,
            ARG_ROUNDING,
        ]
        # Check that the thickness value fits in the allowed values
        if graphic_format.get(ARG_THICKNESS) is not None:
            graphic_format[ARG_THICKNESS] = self._enforce(graphic_format[ARG_THICKNESS])
        # Check that the width value fits in the allowed values
        if graphic_format.get(ARG_WIDTH) is not None:
            graphic_format[ARG_WIDTH] = self._enforce(
                graphic_format[ARG_WIDTH], minimum=graphic_format[ARG_THICKNESS]
            )
        # Check that the height value fits in the allowed values
        if graphic_format.get(ARG_HEIGHT) is not None:
            graphic_format[ARG_HEIGHT] = self._enforce(
                graphic_format[ARG_HEIGHT], minimum=graphic_format[ARG_THICKNESS]
            )
        # Check that the rounding value fits in the allowed values
        if graphic_format.get(ARG_ROUNDING) is not None:
            graphic_format[ARG_ROUNDING] = self._enforce(
                graphic_format[ARG_ROUNDING], minimum=0, maximum=8
            )
        # Generate the ZPL II command
        command = "{origin}{data}{stop}".format(
            origin=self._field_origin(right, down),
            data="^GB" + self._generate_arguments(arguments, graphic_format),
            stop=self._field_data_stop(),
        )
        self._write_command(command)

    def graphic_diagonal_line(self, right, down, graphic_format):
        """Send the commands to draw a rectangle"""
        arguments = [
            ARG_WIDTH,
            ARG_HEIGHT,
            ARG_THICKNESS,
            ARG_COLOR,
            ARG_DIAGONAL_ORIENTATION,
        ]
        # Check that the thickness value fits in the allowed values
        if graphic_format.get(ARG_THICKNESS) is not None:
            graphic_format[ARG_THICKNESS] = self._enforce(graphic_format[ARG_THICKNESS])
        # Check that the width value fits in the allowed values
        if graphic_format.get(ARG_WIDTH) is not None:
            graphic_format[ARG_WIDTH] = self._enforce(
                graphic_format[ARG_WIDTH], minimum=3
            )
        # Check that the height value fits in the allowed values
        if graphic_format.get(ARG_HEIGHT) is not None:
            graphic_format[ARG_HEIGHT] = self._enforce(
                graphic_format[ARG_HEIGHT], minimum=3
            )
        # Check the given orientation
        graphic_format[ARG_DIAGONAL_ORIENTATION] = graphic_format.get(
            ARG_DIAGONAL_ORIENTATION, DIAGONAL_ORIENTATION_LEFT
        )
        # Generate the ZPL II command
        command = "{origin}{data}{stop}".format(
            origin=self._field_origin(right, down),
            data="^GD" + self._generate_arguments(arguments, graphic_format),
            stop=self._field_data_stop(),
        )
        self._write_command(command)

    def graphic_circle(self, right, down, graphic_format):
        """Send the commands to draw a circle"""
        arguments = [ARG_DIAMETER, ARG_THICKNESS, ARG_COLOR]
        # Check that the diameter value fits in the allowed values
        if graphic_format.get(ARG_DIAMETER) is not None:
            graphic_format[ARG_DIAMETER] = self._enforce(
                graphic_format[ARG_DIAMETER], minimum=3, maximum=4095
            )
        # Check that the thickness value fits in the allowed values
        if graphic_format.get(ARG_THICKNESS) is not None:
            graphic_format[ARG_THICKNESS] = self._enforce(
                graphic_format[ARG_THICKNESS], minimum=2, maximum=4095
            )
        # Generate the ZPL II command
        command = "{origin}{data}{stop}".format(
            origin=self._field_origin(right, down),
            data="^GC" + self._generate_arguments(arguments, graphic_format),
            stop=self._field_data_stop(),
        )
        self._write_command(command)

    def graphic_field(self, right, down, pil_image):
        """Encode a PIL image into an ASCII string suitable for ZPL printers"""
        width, height = pil_image.size
        rounded_width = int(math.ceil(width / 8.0) * 8)
        # Transform the image :
        #   - Invert the colors (PIL uses 0 for black, ZPL uses 0 for white)
        #   - Convert to monochrome in case it is not already
        #   - Round the width to a multiple of 8 because ZPL needs an integer
        #     count of bytes per line (each pixel is a bit)
        pil_image = (
            ImageOps.invert(pil_image).convert("1").crop((0, 0, rounded_width, height))
        )
        # Convert the image to a two-character hexadecimal values string
        ascii_data = binascii.hexlify(pil_image.tobytes()).upper()
        # Each byte is composed of two characters
        bytes_per_row = rounded_width / 8
        total_bytes = bytes_per_row * height
        graphic_image_command = (
            "^GFA,{total_bytes},{total_bytes},{bytes_per_row},{ascii_data}".format(
                total_bytes=total_bytes,
                bytes_per_row=bytes_per_row,
                ascii_data=ascii_data,
            )
        )
        # Generate the ZPL II command
        command = "{origin}{data}{stop}".format(
            origin=self._field_origin(right, down),
            data=graphic_image_command,
            stop=self._field_data_stop(),
        )
        self._write_command(command)
