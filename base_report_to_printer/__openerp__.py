# -*- coding: utf-8 -*-
# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Report to printer",
    'version': '9.0.1.0.0',
    'category': 'Generic Modules/Base',
    'author': "Agile Business Group & Domsense, Pegueroles SCP, NaN,"
              " LasLabs, Odoo Community Association (OCA)",
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    "depends": ['report'],
    'data': [
        'data/printing_data.xml',
        'security/security.xml',
        'views/assets.xml',
        'views/printing_printer_view.xml',
        'views/printing_report_view.xml',
        'views/res_users_view.xml',
        'views/ir_actions_report_xml_view.xml',
        'wizards/printing_printer_update_wizard_view.xml',
    ],
    'installable': False,
    'application': True,
    'external_dependencies': {
        'python': ['cups'],
    },
}
