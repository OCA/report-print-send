# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
import base64
import datetime
import io
import logging
import requests
from PIL import Image, ImageOps
from odoo import api, exceptions, fields, models, _
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    import zpl2
except ImportError:
    _logger.debug('Cannot `import zpl2`.')


class PrintingLabelZpl2(models.Model):
    _name = 'printing.label.zpl2'
    _description = 'ZPL II Label'
    _order = 'model_id, name, id'

    name = fields.Char(required=True, help='Label Name.')
    active = fields.Boolean(default=True)
    description = fields.Char(help='Long description for this label.')
    model_id = fields.Many2one(
        comodel_name='ir.model', string='Model', required=True,
        help='Model used to print this label.')
    origin_x = fields.Integer(
        required=True, default=10,
        help='Origin point of the contents in the label, X coordinate.')
    origin_y = fields.Integer(
        required=True, default=10,
        help='Origin point of the contents in the label, Y coordinate.')
    width = fields.Integer(
        required=True, default=480,
        help='Width of the label, will be set on the printer before printing.')
    component_ids = fields.One2many(
        comodel_name='printing.label.zpl2.component', inverse_name='label_id',
        string='Label Components',
        help='Components which will be printed on the label.')
    restore_saved_config = fields.Boolean(
        string="Restore printer's configuration",
        help="Restore printer's saved configuration and end of each label ",
        default=True)
    test_labelary_mode = fields.Boolean(string='Mode Labelary')
    record_id = fields.Integer(string='Record ID', default=1)
    extra = fields.Text(string="Extra", default='{}')
    labelary_image = fields.Binary(string='Image from Labelary', readonly=True)
    labelary_dpmm = fields.Selection(
        selection=[
            ('6dpmm', '6dpmm (152 pdi)'),
            ('8dpmm', '8dpmm (203 dpi)'),
            ('12dpmm', '12dpmm (300 pdi)'),
            ('24dpmm', '24dpmm (600 dpi)'),
        ], string='Print density', required=True, default='8dpmm')
    labelary_width = fields.Float(string='Width in mm', default=140)
    labelary_height = fields.Float(string='Height in mm', default=70)

    def _generate_zpl2_components_data(
            self, label_data, record, page_number=1, page_count=1,
            label_offset_x=0, label_offset_y=0, **extra):
        self.ensure_one()

        # Add all elements to print in a list of tuples :
        #   [(component, data, offset_x, offset_y)]
        to_print = []
        for component in self.component_ids:
            eval_args = extra
            eval_args.update({
                'object': record,
                'page_number': str(page_number + 1),
                'page_count': str(page_count),
                'time': time,
                'datetime': datetime,
            })
            data = safe_eval(component.data, eval_args) or ''

            # Generate a list of elements if the component is repeatable
            for idx in range(
                    component.repeat_offset,
                    component.repeat_offset + component.repeat_count):
                printed_data = data
                # Pick the right value if data is a collection
                if isinstance(data, (list, tuple, set, models.BaseModel)):
                    # If we reached the end of data, quit the loop
                    if idx >= len(data):
                        break

                    # Set the real data to display
                    printed_data = data[idx]

                position = idx - component.repeat_offset
                to_print.append((
                    component, printed_data,
                    label_offset_x + component.repeat_offset_x * position,
                    label_offset_y + component.repeat_offset_y * position,
                ))

        for (component, data, offset_x, offset_y) in to_print:
            component_offset_x = component.origin_x + offset_x
            component_offset_y = component.origin_y + offset_y
            if component.component_type == 'text':
                barcode_arguments = dict([
                    (field_name, component[field_name])
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
                ])
                label_data.font_data(
                    component_offset_x, component_offset_y,
                    barcode_arguments, data)
            elif component.component_type == 'zpl2_raw':
                label_data._write_command(data)
            elif component.component_type == 'rectangle':
                label_data.graphic_box(
                    component_offset_x, component_offset_y, {
                        zpl2.ARG_WIDTH: component.width,
                        zpl2.ARG_HEIGHT: component.height,
                        zpl2.ARG_THICKNESS: component.thickness,
                        zpl2.ARG_COLOR: component.color,
                        zpl2.ARG_ROUNDING: component.rounding,
                    })
            elif component.component_type == 'diagonal':
                label_data.graphic_diagonal_line(
                    component_offset_x, component_offset_y, {
                        zpl2.ARG_WIDTH: component.width,
                        zpl2.ARG_HEIGHT: component.height,
                        zpl2.ARG_THICKNESS: component.thickness,
                        zpl2.ARG_COLOR: component.color,
                        zpl2.ARG_DIAGONAL_ORIENTATION:
                        component.diagonal_orientation,
                    })
            elif component.component_type == 'graphic':
                image = component.graphic_image or data
                pil_image = Image.open(io.BytesIO(
                    base64.b64decode(image))).convert('RGB')
                if component.width and component.height:
                    pil_image = pil_image.resize(
                        (component.width, component.height))

                # Invert the colors
                if component.reverse_print:
                    pil_image = ImageOps.invert(pil_image)

                # Rotation (PIL rotates counter clockwise)
                if component.orientation == zpl2.ORIENTATION_ROTATED:
                    pil_image = pil_image.transpose(Image.ROTATE_270)
                elif component.orientation == zpl2.ORIENTATION_INVERTED:
                    pil_image = pil_image.transpose(Image.ROTATE_180)
                elif component.orientation == zpl2.ORIENTATION_BOTTOM_UP:
                    pil_image = pil_image.transpose(Image.ROTATE_90)

                label_data.graphic_field(
                    component_offset_x, component_offset_y,
                    pil_image
                )
            elif component.component_type == 'circle':
                label_data.graphic_circle(
                    component_offset_x, component_offset_y, {
                        zpl2.ARG_DIAMETER: component.width,
                        zpl2.ARG_THICKNESS: component.thickness,
                        zpl2.ARG_COLOR: component.color,
                    })
            elif component.component_type == 'sublabel':
                component_offset_x += component.sublabel_id.origin_x
                component_offset_y += component.sublabel_id.origin_y
                component.sublabel_id._generate_zpl2_components_data(
                    label_data, data,
                    label_offset_x=component_offset_x,
                    label_offset_y=component_offset_y)
            else:
                if component.component_type == zpl2.BARCODE_QR_CODE:
                    # Adding Control Arguments to QRCode data Label
                    data = 'MM,A{}'.format(data)

                barcode_arguments = dict([
                    (field_name, component[field_name])
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
                ])
                label_data.barcode_data(
                    component.origin_x + offset_x,
                    component.origin_y + offset_y,
                    component.component_type, barcode_arguments, data)

    def _generate_zpl2_data(self, record, page_count=1, **extra):
        self.ensure_one()
        label_data = zpl2.Zpl2()

        labelary_emul = extra.get('labelary_emul', False)
        for page_number in range(page_count):
            # Initialize printer's configuration
            label_data.label_start()
            if not labelary_emul:
                label_data.print_width(self.width)
            label_data.label_encoding()

            label_data.label_home(self.origin_x, self.origin_y)

            self._generate_zpl2_components_data(
                label_data, record, page_number=page_number,
                page_count=page_count, **extra)

            # Restore printer's configuration and end the label
            if self.restore_saved_config:
                label_data.configuration_update(zpl2.CONF_RECALL_LAST_SAVED)
            label_data.label_end()

        return label_data.output()

    def render_label(self, record, page_count=1, **extra):
        res = ""
        for label in self:
            if record._name != label.model_id.model:
                raise exceptions.UserError(
                    _('This label cannot be used on {model}').format(
                        model=record._name))
            if len(res) > 0:
                res += "\n"
            # Send the label to printer
            res += label._generate_zpl2_data(
                record, page_count=page_count, **extra).decode('utf-8')
        return res

    def import_zpl2(self):
        self.ensure_one()
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.import.zpl2',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_label_id': self.id},
        }

    def _get_record(self):
        self.ensure_one()
        Obj = self.env[self.model_id.model]
        record = Obj.search([('id', '=', self.record_id)], limit=1)
        if not record:
            record = Obj.search([], limit=1, order='id desc')
            self.record_id = record.id
        return record

    @api.onchange(
        'record_id', 'labelary_dpmm', 'labelary_width', 'labelary_height',
        'component_ids', 'origin_x', 'origin_y')
    def _on_change_labelary(self):
        self.ensure_one()
        if not(self.test_labelary_mode and self.record_id and
                self.labelary_width and self.labelary_height and
                self.labelary_dpmm and self.component_ids):
            return
        record = self._get_record()
        if record:
            # If case there an error (in the data field with the safe_eval
            # for exemple) the new component or the update is not lost.
            try:
                url = 'http://api.labelary.com/v1/printers/' \
                    '{dpmm}/labels/{width}x{height}/0/'
                width = round(self.labelary_width / 25.4, 2)
                height = round(self.labelary_height / 25.4, 2)
                url = url.format(
                    dpmm=self.labelary_dpmm, width=width, height=height)
                extra = safe_eval(self.extra, {'env': self.env})
                zpl_file = self._generate_zpl2_data(
                    record, labelary_emul=True, **extra)
                files = {'file': zpl_file}
                headers = {'Accept': 'image/png'}
                response = requests.post(
                    url, headers=headers, files=files, stream=True)
                if response.status_code == 200:
                    # Add a padd
                    im = Image.open(io.BytesIO(response.content))
                    im_size = im.size
                    new_im = Image.new(
                        'RGB', (im_size[0] + 2, im_size[1] + 2),
                        (164, 164, 164))
                    new_im.paste(im, (1, 1))
                    imgByteArr = io.BytesIO()
                    new_im.save(imgByteArr, format='PNG')
                    self.labelary_image = base64.b64encode(
                        imgByteArr.getvalue())
                else:
                    return {'warning': {
                        'title': _('Error with Labelary API.'),
                        'message': response.status_code,
                    }}

            except Exception as e:
                self.labelary_image = False
                return {'warning': {
                    'title': _('Some thing is wrong.'),
                    'message': e,
                }}
