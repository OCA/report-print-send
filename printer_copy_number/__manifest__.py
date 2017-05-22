# -*- coding: utf-8 -*-

{
    'name': 'Report to printer - Copies',
    'version': '10.0.1.0.0',
    'category': 'Printer',
    'description': 'Allow to specify copies on report',
    'author': "Apertoso N.V., Odoo Community Association (OCA)",
    'maintainer': 'Apertoso',
    'website': 'http://www.apertoso.be/',
    'license': 'AGPL-3',
    'depends': [
        'base_report_to_printer',
    ],
    'data': [
        'views/ir_actions_report_xml.xml',
        'views/printing_report_xml_action.xml',
        'views/res_users.xml',
    ],
    'external_dependencies': {
        'python': ['cups'],
    },
    'installable': True,
    'application': True,
}
