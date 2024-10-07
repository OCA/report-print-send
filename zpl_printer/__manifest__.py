{
    "name": "ZPL Printer Management",
    "version": "16.0.0.0.1",
    "category": "Manufacturing",
    "summary": "Allows easy management of ZPL-Printers, connects to printers through their URL",
    "author": "Voltfang GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/report-print-send",
    "license": "AGPL-3",
    "depends": ["base_setup"],
    "data": ["security/ir.model.access.csv", "views/zpl_printer_view.xml"],
    "assets": {
        "web.assets_backend": [
            "zpl_printer/static/src/js/zplactionmanager.esm.js",
        ]
    },
    "installable": True,
}
