# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    'name': 'pingen.com server environment',
    'version': '10.0.1.0.0',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'maintainer': 'Camptocamp',
    'license': 'AGPL-3',
    'category': 'Reporting',
    'complexity': 'easy',
    'depends': ['pingen','server_environment','base_setup'],
    'website': 'http://www.camptocamp.com',
    'data': [
    	"views/res_company_views.xml",
        ],
    'tests': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
