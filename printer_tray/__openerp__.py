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
{'name': 'Report to printer - Paper tray selection',
 'version': '1.0',
 'category': 'Printer',
 'description': """
Report to printer - Paper tray selection
========================================

 **Author:** Camptocamp SA

 *This module extends `Report to printer` module.*

 It detects trays on printer installation plus permits to select
 the paper source on which you want to print directly.

 You will find this option on default user config, on default report config
 and on specific config per user per report.

 This allows you to dedicate a specific paper source for exemple for prepinted
 paper such as payment slip.
 """,
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'website': 'http://www.camptocamp.com/',
 'depends': ['base_report_assembler',
             'base_report_to_printer',
             ],
 'data': [
     'users_view.xml',
     'ir_report_view.xml',
     ],
 'test': [],
 'installable': True,
 'auto_install': False,
 'application': True,
 }
