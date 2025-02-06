# Copyright (C) 2022 Raumschmiede GmbH - Christopher Hansen (<https://www.raumschmiede.de>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Report to label printer",
    "version": "16.0.1.0.1",
    "category": "Generic Modules/Base",
    "author": "Raumschmiede GmbH - Christopher Hansen,"
    " Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/report-print-send",
    "license": "AGPL-3",
    "depends": ["base_report_to_printer"],
    "data": [
        "views/res_users.xml",
        "views/ir_actions_report.xml",
    ],
    "installable": True,
    "application": False,
}
