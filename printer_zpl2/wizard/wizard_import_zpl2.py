# Copyright (C) 2018 Florent Mirieu (<https://github.com/fmdl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import re
import base64
import binascii
import io


from PIL import Image, ImageOps
from odoo import fields, models, _

_logger = logging.getLogger(__name__)

try:
    import zpl2
except ImportError:
    _logger.debug('Cannot `import zpl2`.')


def _compute_arg(data, arg):
    vals = {}
    for i, d in enumerate(data.split(',')):
        vals[arg[i]] = d
    return vals


def _field_origin(data):
    if data[:2] == 'FO':
        position = data[2:]
        vals = _compute_arg(position, ['origin_x', 'origin_y'])
        return vals
    return {}


def _font_format(data):
    if data[:1] == 'A':
        data = data.split(',')
        vals = {}
        if len(data[0]) > 1:
            vals[zpl2.ARG_FONT] = data[0][1]
        if len(data[0]) > 2:
            vals[zpl2.ARG_ORIENTATION] = data[0][2]

        if len(data) > 1:
            vals[zpl2.ARG_HEIGHT] = data[1]
        if len(data) > 2:
            vals[zpl2.ARG_WIDTH] = data[2]
        return vals
    return {}


def _default_font_format(data):
    if data[:2] == 'CF':
        args = [
            zpl2.ARG_FONT,
            zpl2.ARG_HEIGHT,
            zpl2.ARG_WIDTH,
        ]
        vals = _compute_arg(data[2:], args)
        if vals.get(zpl2.ARG_HEIGHT, False) \
                and not vals.get(zpl2.ARG_WIDTH, False):
            vals.update({zpl2.ARG_WIDTH: vals.get(zpl2.ARG_HEIGHT)})
        else:
            vals.update({zpl2.ARG_HEIGHT: 10, zpl2.ARG_HEIGHT: 10})
        return vals
    return {}


def _field_block(data):
    if data[:2] == 'FB':
        vals = {zpl2.ARG_IN_BLOCK: True}
        args = [
            zpl2.ARG_BLOCK_WIDTH,
            zpl2.ARG_BLOCK_LINES,
            zpl2.ARG_BLOCK_SPACES,
            zpl2.ARG_BLOCK_JUSTIFY,
            zpl2.ARG_BLOCK_LEFT_MARGIN,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _code11(data):
    if data[:2] == 'B1':
        vals = {'component_type': zpl2.BARCODE_CODE_11}
        args = [
            zpl2.ARG_ORIENTATION,
            zpl2.ARG_CHECK_DIGITS,
            zpl2.ARG_HEIGHT,
            zpl2.ARG_INTERPRETATION_LINE,
            zpl2.ARG_INTERPRETATION_LINE_ABOVE,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _interleaved2of5(data):
    if data[:2] == 'B2':
        vals = {'component_type': zpl2.BARCODE_INTERLEAVED_2_OF_5}
        args = [
            zpl2.ARG_ORIENTATION,
            zpl2.ARG_HEIGHT,
            zpl2.ARG_INTERPRETATION_LINE,
            zpl2.ARG_INTERPRETATION_LINE_ABOVE,
            zpl2.ARG_CHECK_DIGITS,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _code39(data):
    if data[:2] == 'B3':
        vals = {'component_type': zpl2.BARCODE_CODE_39}
        args = [
            zpl2.ARG_ORIENTATION,
            zpl2.ARG_CHECK_DIGITS,
            zpl2.ARG_HEIGHT,
            zpl2.ARG_INTERPRETATION_LINE,
            zpl2.ARG_INTERPRETATION_LINE_ABOVE,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _code49(data):
    if data[:2] == 'B4':
        vals = {'component_type': zpl2.BARCODE_CODE_49}
        args = [
            zpl2.ARG_ORIENTATION,
            zpl2.ARG_HEIGHT,
            zpl2.ARG_INTERPRETATION_LINE,
            zpl2.ARG_STARTING_MODE,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _pdf417(data):
    if data[:2] == 'B7':
        vals = {'component_type': zpl2.BARCODE_PDF417}
        args = [
            zpl2.ARG_ORIENTATION,
            zpl2.ARG_HEIGHT,
            zpl2.ARG_SECURITY_LEVEL,
            zpl2.ARG_COLUMNS_COUNT,
            zpl2.ARG_ROWS_COUNT,
            zpl2.ARG_TRUNCATE,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _ean8(data):
    if data[:2] == 'B8':
        vals = {'component_type': zpl2.BARCODE_EAN_8}
        args = [
            zpl2.ARG_ORIENTATION,
            zpl2.ARG_HEIGHT,
            zpl2.ARG_INTERPRETATION_LINE,
            zpl2.ARG_INTERPRETATION_LINE_ABOVE,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _upce(data):
    if data[:2] == 'B9':
        vals = {'component_type': zpl2.BARCODE_UPC_E}
        args = [
            zpl2.ARG_ORIENTATION,
            zpl2.ARG_HEIGHT,
            zpl2.ARG_INTERPRETATION_LINE,
            zpl2.ARG_INTERPRETATION_LINE_ABOVE,
            zpl2.ARG_CHECK_DIGITS,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _code128(data):
    if data[:2] == 'BC':
        vals = {'component_type': zpl2.BARCODE_CODE_128}
        args = [
            zpl2.ARG_ORIENTATION,
            zpl2.ARG_HEIGHT,
            zpl2.ARG_INTERPRETATION_LINE,
            zpl2.ARG_INTERPRETATION_LINE_ABOVE,
            zpl2.ARG_CHECK_DIGITS,
            zpl2.ARG_MODE,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _ean13(data):
    if data[:2] == 'BE':
        vals = {'component_type': zpl2.BARCODE_EAN_13}
        args = [
            zpl2.ARG_ORIENTATION,
            zpl2.ARG_HEIGHT,
            zpl2.ARG_INTERPRETATION_LINE,
            zpl2.ARG_INTERPRETATION_LINE_ABOVE,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _qrcode(data):
    if data[:2] == 'BQ':
        vals = {'component_type': zpl2.BARCODE_QR_CODE}
        args = [
            zpl2.ARG_ORIENTATION,
            zpl2.ARG_MODEL,
            zpl2.ARG_MAGNIFICATION_FACTOR,
            zpl2.ARG_ERROR_CORRECTION,
            zpl2.ARG_MASK_VALUE,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _default_barcode_field(data):
    if data[:2] == 'BY':
        args = [
            zpl2.ARG_MODULE_WIDTH,
            zpl2.ARG_BAR_WIDTH_RATIO,
            zpl2.ARG_HEIGHT,
        ]
        return _compute_arg(data[2:], args)
    return {}


def _field_reverse_print(data):
    if data[:2] == 'FR':
        return {zpl2.ARG_REVERSE_PRINT: True}
    return {}


def _graphic_box(data):
    if data[:2] == 'GB':
        vals = {'component_type': 'rectangle'}
        args = [
            zpl2.ARG_WIDTH,
            zpl2.ARG_HEIGHT,
            zpl2.ARG_THICKNESS,
            zpl2.ARG_COLOR,
            zpl2.ARG_ROUNDING,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _graphic_circle(data):
    if data[:2] == 'GC':
        vals = {'component_type': 'circle'}
        args = [
            zpl2.ARG_WIDTH,
            zpl2.ARG_THICKNESS,
            zpl2.ARG_COLOR,
        ]
        vals.update(_compute_arg(data[2:], args))
        return vals
    return {}


def _graphic_field(data):
    if data[:3] == 'GFA':
        vals = {}
        args = [
            'compression',
            'total_bytes',
            'total_bytes',
            'bytes_per_row',
            'ascii_data',
        ]
        vals.update(_compute_arg(data[3:], args))

        # Image
        rawData = re.sub('[^A-F0-9]+', '', vals['ascii_data'])
        rawData = binascii.unhexlify(rawData)

        width = int(float(vals['bytes_per_row']) * 8)
        height = int(float(vals['total_bytes']) / width) * 8

        img = Image.frombytes(
            '1', (width, height), rawData, 'raw').convert('L')
        img = ImageOps.invert(img)

        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        image = base64.b64encode(imgByteArr.getvalue())

        return {
            'component_type': 'graphic',
            'graphic_image': image,
            zpl2.ARG_WIDTH: width,
            zpl2.ARG_HEIGHT: height,
        }
    return {}


def _get_data(data):
    if data[:2] == 'FD':
        return {'data': '"%s"' % data[2:]}
    return {}


SUPPORTED_CODE = {
    'FO': {'method': _field_origin},
    'FD': {'method': _get_data},
    'A': {'method': _font_format},
    'FB': {'method': _field_block},
    'B1': {'method': _code11},
    'B2': {'method': _interleaved2of5},
    'B3': {'method': _code39},
    'B4': {'method': _code49},
    'B7': {'method': _pdf417},
    'B8': {'method': _ean8},
    'B9': {'method': _upce},
    'BC': {'method': _code128},
    'BE': {'method': _ean13},
    'BQ': {'method': _qrcode},
    'BY': {
        'method': _default_barcode_field,
        'default': [
            zpl2.BARCODE_CODE_11,
            zpl2.BARCODE_INTERLEAVED_2_OF_5,
            zpl2.BARCODE_CODE_39,
            zpl2.BARCODE_CODE_49,
            zpl2.BARCODE_PDF417,
            zpl2.BARCODE_EAN_8,
            zpl2.BARCODE_UPC_E,
            zpl2.BARCODE_CODE_128,
            zpl2.BARCODE_EAN_13,
            zpl2.BARCODE_QR_CODE,
        ],
    },
    'CF': {'method': _default_font_format, 'default': ['text']},
    'FR': {'method': _field_reverse_print},
    'GB': {'method': _graphic_box},
    'GC': {'method': _graphic_circle},
    'GFA': {'method': _graphic_field},
}


class WizardImportZPl2(models.TransientModel):
    _name = 'wizard.import.zpl2'
    _description = 'Import ZPL2'

    label_id = fields.Many2one(
        comodel_name='printing.label.zpl2', string='Label',
        required=True, readonly=True,)
    data = fields.Text(
        required=True, help='Printer used to print the labels.')
    delete_component = fields.Boolean(
        string='Delete existing components', default=False)

    def _start_sequence(self):
        sequences = self.mapped('label_id.component_ids.sequence')
        if sequences:
            return max(sequences) + 1
        return 0

    def import_zpl2(self):
        Zpl2Component = self.env['printing.label.zpl2.component']

        if self.delete_component:
            self.mapped('label_id.component_ids').unlink()

        Model = self.env['printing.label.zpl2.component']
        self.model_fields = Model.fields_get()
        sequence = self._start_sequence()
        default = {}

        for i, line in enumerate(self.data.split('\n')):
            vals = {}

            args = line.split('^')
            for arg in args:
                for key, code in SUPPORTED_CODE.items():
                    component_arg = code['method'](arg)
                    if component_arg:
                        if code.get('default', False):
                            for deft in code.get('default'):
                                default.update({deft: component_arg})
                        else:
                            vals.update(component_arg)
                        break

            if vals:
                if 'component_type' not in vals.keys():
                    vals.update({'component_type': 'text'})

                if vals['component_type'] in default.keys():
                    vals.update(default[vals['component_type']])

                vals = self._update_vals(vals)

                seq = sequence + i * 10
                vals.update({
                    'name': _('Import %s') % seq,
                    'sequence': seq,
                    'label_id': self.label_id.id,
                })
                Zpl2Component.create(vals)

    def _update_vals(self, vals):
        if 'orientation' in vals.keys() and vals['orientation'] == '':
            vals['orientation'] = 'N'

        # Field
        component = {}
        for field, value in vals.items():
            if field in self.model_fields.keys():
                field_type = self.model_fields[field].get('type', False)
                if field_type == 'boolean':
                    if not value or value == zpl2.BOOL_NO:
                        value = False
                    else:
                        value = True
                if field_type in ('integer', 'float'):
                    value = float(value)
                if field == 'model':
                    value = int(float(value))
                component.update({field: value})
        return component
