#  Copyright 2020 Simone Rubino - Agile Business Group
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import io

from odoo import api, models
from pylibdmtx.pylibdmtx import encode
from PIL import Image


class IrActionsReport (models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def barcode(self, barcode_type, value,
                width=600, height=100, humanreadable=0):

        if barcode_type == 'AutoDatamatrix':
            encoded = encode(value.encode('utf8'))
            img_size = (encoded.width, encoded.height)
            img = Image.frombytes('RGB', img_size, encoded.pixels)
            with io.BytesIO() as output:
                img.save(output, format="PNG")
                return output.getvalue()

        return super().barcode(
            barcode_type, value,
            width=width, height=height, humanreadable=humanreadable)
