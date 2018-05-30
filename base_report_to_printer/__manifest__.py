# -*- coding: utf-8 -*-
# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Report to printer",
    'version': '10.0.2.0.2',
    'category': 'Generic Modules/Base',
    'author': "Agile Business Group & Domsense, Pegueroles SCP, NaN, "
              "LasLabs, Tecnativa, Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/report-print-send',
    'license': 'AGPL-3',
    "depends": ['report'],
    'data': [
        'data/printing_data.xml',
        'security/security.xml',
        'views/assets.xml',
        'views/printing_printer_view.xml',
        'views/printing_server.xml',
        'views/printing_job.xml',
        'views/printing_report_view.xml',
        'views/res_users_view.xml',
        'views/ir_actions_report_xml_view.xml',
        'wizards/printing_printer_update_wizard_view.xml',
    ],
    'demo': [
        'demo/report.xml',
    ],
    'installable': True,
    'application': True,
    'external_dependencies': {
        'python': ['cups'],
    },
}
