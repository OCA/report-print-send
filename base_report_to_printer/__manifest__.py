# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Report to printer",
    "version": "16.0.1.1.8",
    "category": "Generic Modules/Base",
    "author": "Agile Business Group & Domsense, Pegueroles SCP, NaN,"
    " LasLabs, Camptocamp, Odoo Community Association (OCA),"
    " Open for Small Business Ltd",
    "website": "https://github.com/OCA/report-print-send",
    "license": "AGPL-3",
    "depends": ["web"],
    "data": [
        "data/printing_data.xml",
        "security/security.xml",
        "views/printing_printer.xml",
        "views/printing_server.xml",
        "views/printing_job.xml",
        "views/printing_report.xml",
        "views/res_users.xml",
        "views/ir_actions_report.xml",
        "wizards/print_attachment_report.xml",
        "wizards/printing_printer_update_wizard_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/base_report_to_printer/static/src/js/qweb_action_manager.esm.js",
        ],
    },
    "installable": True,
    "application": False,
    "external_dependencies": {"python": ["pycups"]},
}
