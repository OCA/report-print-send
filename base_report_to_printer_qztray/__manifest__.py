# Copyright (C) 2022 PESOL (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Report to QZ Tray",
    "version": "19.0.1.0.1",
    "category": "Generic Modules/Base",
    "author": "PESOL, Nagarro, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/report-print-send",
    "license": "AGPL-3",
    "depends": ["base_report_to_printer"],
    "data": [
        "views/assets.xml",
    ],
    "installable": True,
    "application": False,
    "external_dependencies": {"python": ["pyOpenSSL"]},
    "assets": {
        "web.assets_backend": [
            "base_report_to_printer_qztray/static/src/js/qweb_action_manager.esm.js"
        ],
    },
}
