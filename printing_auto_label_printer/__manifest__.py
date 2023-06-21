# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Printing Auto Label Printer",
    "author": "BCIM, MT Software, Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux"],
    "category": "Warehouse Management",
    "data": [
        "views/printing_auto.xml",
    ],
    "depends": [
        "base_report_to_label_printer",
        "printing_auto_base",
    ],
    "auto_install": True,
    "license": "AGPL-3",
    "version": "14.0.1.0.0",
    "website": "https://github.com/OCA/report-print-send",
}
