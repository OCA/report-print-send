# noinspection PyStatementEffect
{
    'name': 'Automatic Print Rules',
    'version': '11.0.1.0.0',
    'author': 'O4SB',
    'website': 'https://o4sb.com',
    'depends': ['base_report_to_printer', 'queue_job', 'base_automation'],
    "summary": 'This module allows to select printer based on properties of '
               'record being printed',
    'data': [
             'views/ir_actions_report.xml',
             'views/ir_actions_server.xml',
             ],

}