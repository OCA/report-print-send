# -*- coding: utf-8 -*-
# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Printer ZPL II',
    'version': '10.0.1.1.2',
    'category': 'Printer',
    'author': 'SYLEAM, Odoo Community Association (OCA)',
    'website': 'http://www.syleam.fr/',
    'license': 'AGPL-3',
    'external_dependencies': {
        'python': ['zpl2'],
    },
    'depends': [
        'base_report_to_printer',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/printing_label_zpl2.xml',
        'wizard/print_record_label.xml',
    ],
    'installable': True,
}
