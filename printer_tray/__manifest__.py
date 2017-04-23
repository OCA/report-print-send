# -*- coding: utf-8 -*-
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Report to printer - Paper tray selection',
    'version': '10.0.1.0.0',
    'category': 'Printer',
    'author': "Camptocamp, Odoo Community Association (OCA)",
    'maintainer': 'Camptocamp',
    'website': 'http://www.camptocamp.com/',
    'license': 'AGPL-3',
    'depends': [
        'base_report_to_printer',
    ],
    'data': [
        'views/res_users.xml',
        'views/ir_actions_report_xml.xml',
        'views/printing_printer.xml',
        'views/printing_report_xml_action.xml',
        'security/ir.model.access.csv',
    ],
    'external_dependencies': {
        'python': ['cups'],
    },
    'installable': True,
    'application': True,
}
