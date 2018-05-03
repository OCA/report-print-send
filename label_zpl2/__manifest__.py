# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Label ZPL II',
    'version': '11.0.1.0.0',
    'category': 'Printer',
    'author': 'SYLEAM, Apertoso NV, Odoo Community Association (OCA)',
    'website': 'http://www.syleam.fr/',
    'license': 'AGPL-3',
    'external_dependencies': {
        'python': ['zpl2'],
    },
    'depends': [
        'base', 'web'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/printing_label_zpl2.xml',
        'wizard/wizard_import_zpl2.xml',
    ],
    'installable': True,
}
