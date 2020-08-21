# Copyright 2020 Lorenzo Battistini @ TAKOBI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "ZPL II Browser Print",
    "summary": "Print ZPL labels directly from web browser, "
               "using printer installed locally",
    "version": "12.0.1.0.0",
    "development_status": "Beta",
    "category": "Printer",
    "website": "https://github.com/OCA/report-print-send",
    "author": "TAKOBI, Odoo Community Association (OCA)",
    "maintainers": ["eLBati"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "printer_zpl2",
    ],
    "data": [
        "wizard/browser_print_label.xml",
        "views/printing_label_zpl2.xml",
        "views/assets.xml",
    ],
    'qweb': [
        'static/src/xml/browser_print.xml',
    ],
}
