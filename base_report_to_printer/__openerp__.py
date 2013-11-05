# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
#    Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2013 Camptocamp (<http://www.camptocamp.com>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Report to printer",
    'version': '0.1',
    'category': 'Generic Modules/Base',
    'description': """This module allows users to send reports to a printer attached to the server. Settings can be configured globaly, per user, per report and per user and report.
    Before you can use this module:
    You must have lpr installed for this module to work as-is.
    To install lpr on ubuntu enter this command at the CLI - sudo apt-get install cups-bsd
    type  ls | lpr at the command prompt to confirm your server can print

    After installing enable the "Printing / Print Operator" option under access rights to give users the ability to view the print menu.
    Then goto the user profile and set the users printing action and default printer.
    """,
    'author': 'Agile Business Group & Domsense, Pegueroles SCP, NaN',
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    "depends" : ['base', 'base_calendar'],
    'data': [
        'security/security.xml',
        'printing_data.xml',
        'printing_view.xml',
        'wizard/update_printers.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'external_dependencies': {
        'python': ['cups']
        }
}
