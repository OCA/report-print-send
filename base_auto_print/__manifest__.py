# noinspection PyStatementEffect
{
    'name': 'Automatic Print Rules',
    'version': '10.0.1.0.0',
    'author': 'O4SB',
    'website': 'http://www.openforsmallbusiness.co.nz',
    'depends': ['base_report_to_printer', 'queue_job', 'stock', 'mrp', 'sale'],
    "summary": 'This module allows to select printer based on properties of '
               'record being printed',
    'data': [
             'views/ir_actions_report_xml.xml',
             'security/ir.model.access.csv'],

}