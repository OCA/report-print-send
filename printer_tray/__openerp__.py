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
 'version': '8.0.1.0.1',
 'category': 'Printer',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'website': 'http://www.camptocamp.com/',
 'license': 'AGPL-3',
 'depends': ['base_report_to_printer',
             ],
 'data': [
     'users_view.xml',
     'ir_report_view.xml',
     'printer_view.xml',
     'report_xml_action_view.xml',
     'security/ir.model.access.csv',
     ],
 'external_dependencies': {
     'python': ['cups'],
 },
 'installable': True,
 'auto_install': False,
 'application': True,
 }
