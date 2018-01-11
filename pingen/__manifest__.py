# -*- coding: utf-8 -*-
# Author: Guewen Baconnier
# Copyright 2012-2017 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'pingen.com integration',
    'version': '10.0.1.0.0',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'maintainer': 'Camptocamp',
    'license': 'AGPL-3',
    'category': 'Reporting',
    'complexity': 'easy',
    'depends': ['base_setup'],
    'external_dependencies': {
        'python': ['requests'],
        },
    'website': 'http://www.camptocamp.com',
    'data': [
        'views/ir_attachment_view.xml',
        'views/pingen_document_view.xml',
        'data/pingen_data.xml',
        'views/base_config_settings.xml',
        'security/ir.model.access.csv',
        ],
    'tests': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
