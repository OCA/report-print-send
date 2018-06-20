# Copyright (c) 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Report to printer on remotes",
    'version': '11.0.2.1.0',
    'category': 'Generic Modules/Base',
    'author': "Creu Blanca, Odoo Community Association (OCA)",
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    "depends": ['base_remote', 'base_report_to_printer'],
    'data': [
        'data/printing_data.xml',
        'security/ir.model.access.csv',
        'views/res_remote_views.xml',
        'views/res_remote_printer_views.xml',
    ],
    'installable': True,
    'application': True,
}
