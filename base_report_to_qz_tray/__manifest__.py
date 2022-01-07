# Copyright (C) 2022 PESOL (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Report to QZ Tray",
    "version": "14.0.1.0.0",
    "category": "Generic Modules/Base",
    "author": "PESOL, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/report-print-send",
    "license": "AGPL-3",
    "depends": ["web", "mail"],
    "data": [
        "security/security.xml",
        "views/assets.xml",
        "views/ir_actions_report.xml",
        "views/res_users.xml",
    ],
    "installable": True,
    "application": False,
    "external_dependencies": {"python": ["pyOpenSSL"]},
}
