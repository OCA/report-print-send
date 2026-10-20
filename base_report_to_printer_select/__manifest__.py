# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Report to printer - Select printer when printing",
    "version": "18.0.1.0.0",
    "category": "Generic Modules/Base",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/report-print-send",
    "license": "AGPL-3",
    "depends": ["base_report_to_printer"],
    "data": [
        "views/printing_printer.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/base_report_to_printer_select/static/src/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
