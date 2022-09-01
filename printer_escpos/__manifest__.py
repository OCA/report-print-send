# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Printer Escpos",
    "summary": "Print ESCPOS tickets using odoo",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "CreuBlanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/report-print-send",
    "depends": ["base_report_to_printer"],
    "data": [
        "wizards/print_record_escpos.xml",
        "security/ir.model.access.csv",
        "views/printing_escpos.xml",
    ],
    "demo": ["demo/demo.xml"],
    "external_dependencies": {"python": ["python-escpos"]},
}
