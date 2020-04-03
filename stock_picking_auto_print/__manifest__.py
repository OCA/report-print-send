# Copyright (C) 2019 IBM Corp.
# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Direct Print",
    "summary": "Auto print when DO is ready",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "category": "Generic Modules/Base",
    "website": "http://www.opensourceintegrators.com",
    "depends": ["sale_stock", "base_report_to_printer"],
    "data": ["views/ir_action_report_view.xml"],
    "maintainers": ["bodedra"],
    "installable": True,
}
