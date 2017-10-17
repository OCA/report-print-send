# -*- coding: utf-8 -*-
# Author: Guewen Baconnier
# Copyright 2012-2017 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields
from .pingen import Pingen


class ResCompany(models.Model):

    _inherit = 'res.company'

    pingen_token = fields.Char('Pingen Token', size=32)
    pingen_staging = fields.Boolean('Pingen Staging')

    def _pingen(self):
        """ Return a Pingen instance to work on """
        self.ensure_one()
        return Pingen(self.pingen_token, staging=self.pingen_staging)
