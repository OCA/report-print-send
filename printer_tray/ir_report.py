# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api


class IrActionsReportXml(models.Model):

    _inherit = 'ir.actions.report.xml'

    printer_tray_id = fields.Many2one(
        comodel_name='printing.tray',
        string='Paper Source',
        domain="[('printer_id', '=', printing_printer_id)]",
    )

    @api.onchange('printing_printer_id')
    def onchange_printing_printer_id(self):
        """ Reset the tray when the printer is changed """
        self.printer_tray_id = False
