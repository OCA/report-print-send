# -*- coding: utf-8 -*-
# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Report to printer",
    'version': '11.0.2.3.0',
    'category': 'Generic Modules/Base',
    'author': "Agile Business Group & Domsense, Pegueroles SCP, NaN,"
              " LasLabs, Camptocamp, Odoo Community Association (OCA)",
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    "depends": ['web'],
    'data': [
        'data/printing_data.xml',
        'security/security.xml',
        'views/assets.xml',
        'views/printing_printer.xml',
        'views/printing_server.xml',
        'views/printing_job.xml',
        'views/printing_report.xml',
        'views/res_users.xml',
        'views/ir_actions_report.xml',
        'wizards/printing_printer_update_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
    'external_dependencies': {
        'python': ['cups'],
    },
}
