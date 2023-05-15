{
    "name": "Printing Simple Configuration",
    "summary": "Allow to set printing configuration in company or in warehouse",
    "version": "16.0.1.0.1",
    "category": "Generic Modules/Base",
    "website": "https://github.com/OCA/report-print-send",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainer": [
        "bealdav",
    ],
    "maturity": "Alpha",
    "license": "AGPL-3",
    "depends": [
        "stock",
    ],
    "data": [
        "views/company.xml",
        "views/print_config.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
    ],
    "demo": [
        "data/demo.xml",
    ],
    "installable": True,
}
