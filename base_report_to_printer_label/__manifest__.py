# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Report to printer (label)",
    "summary": "Adds a label printer configuration to the user.",
    "version": "14.0.1.0.0",
    "category": "Tools",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/report-print-send",
    "development_status": "Beta",
    "license": "AGPL-3",
    "depends": ["base_report_to_printer"],
    "data": ["views/res_users.xml"],
    "installable": True,
    "pre_init_hook": "pre_init_hook",
}
