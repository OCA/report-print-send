# Copyright (c) 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Report to printer on remotes",
    "version": "16.0.1.0.0",
    "category": "Generic Modules/Base",
    "author": "Creu Blanca, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/report-print-send",
    "license": "AGPL-3",
    "depends": ["base_remote", "base_report_to_printer"],
    "data": [
        "views/printing_printer.xml",
        "data/printing_data.xml",
        "security/ir.model.access.csv",
        "views/res_remote_views.xml",
        "views/res_remote_printer_views.xml",
    ],
    "installable": True,
}
