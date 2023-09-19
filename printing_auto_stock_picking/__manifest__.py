# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Printing Auto Stock Picking",
    "author": "BCIM, MT Software, Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux"],
    "category": "Warehouse Management",
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/stock_picking.xml",
        "views/stock_picking_type.xml",
    ],
    "depends": [
        "stock",
        "printing_auto_base",
    ],
    "license": "AGPL-3",
    "version": "14.0.1.0.0",
    "website": "https://github.com/OCA/report-print-send",
}
