# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Report to printer via WebSocket",
    "version": "19.0.1.0.0",
    "category": "Generic Modules/Base",
    "author": "ForgeFlow,Dixmit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/report-print-send",
    "license": "AGPL-3",
    "depends": ["base_report_to_printer", "bus"],
    "data": [
        "views/printing_printer.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/base_report_to_printer_websocket/static/src/js/qweb_action_manager.esm.js",
        ],
    },
    "installable": True,
    "application": False,
}
