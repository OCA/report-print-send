# Copyright 2019 Compassion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=C8101
{
    'name': 'Report to printer - Custom Printer Options',
    'version': '11.0.1.0.0',
    'category': 'Printer',
    'author': 'Compassion CH, OCA',
    'website': 'https://github.com/OCA/report-print-send',
    'license': 'AGPL-3',
    'depends': [
        'base_report_to_printer'        # oca_addons/report-print-send
    ],
    'data': [
        'views/printing_printer.xml',
        'views/ir_actions_reports_xml_view.xml',
        'security/ir.model.access.csv'
    ],
    'external_dependencies': {
        'python': ['cups'],
    },
    'installable': True,
    'application': False,
    'summary': "Adds the ability to check all printing options available "
               "from a CUPS printer set them in the reports",
}
