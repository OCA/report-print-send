# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Report to printer CUPS",
    "version": "19.0.0.2.0",
    "category": "Generic Modules/Base",
    "author": "Agile Business Group & Domsense, Pegueroles SCP, NaN,"
    " LasLabs, Camptocamp, Odoo Community Association (OCA),"
    " Open for Small Business Ltd",
    "website": "https://github.com/OCA/report-print-send",
    "license": "AGPL-3",
    "depends": ["base_report_to_printer"],
    "data": [
        "data/printing_data.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/printing_printer.xml",
        "views/printing_server.xml",
        "views/printing_job.xml",
        "wizards/printing_printer_update_wizard_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/base_report_to_printer_cups/static/src/js/qweb_action_manager.esm.js",
        ],
    },
    "installable": True,
    "application": False,
    "external_dependencies": {"python": ["pycups"]},
}
