# Author: Guewen Baconnier
# Copyright 2012-2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "pingen.com integration",
    "version": "16.0.1.0.1",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["ajaniszewska-dev", "grindtildeath"],
    "license": "AGPL-3",
    "category": "Reporting",
    "maturity": "Production/Stable",
    "depends": ["base_setup"],
    "external_dependencies": {
        "python": ["requests_oauthlib", "oauthlib"],
    },
    "website": "https://github.com/OCA/report-print-send",
    "data": [
        "views/ir_attachment_view.xml",
        "views/pingen_document_view.xml",
        "data/pingen_data.xml",
        "views/base_config_settings.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": True,
}
