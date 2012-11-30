# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
#    Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
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
    'description': """
Extracted from printjob ( http://apps.openerp.com/addon/1727 ), this module allows to send reports to a printer attached to the server. Settings can be configured globaly, per user, per report and per user and report.

Configuration
=============

First of all, you have to load CUPS printers in OpenERP. You can use a wizard that retrieves them automatically. You just have to click on Update Printers from CUPS and printers will appear within the available printers list.

In the next step you will configure the reports to send to the printers.
Through the report form you can define the system’s behaviour while producing the report.

You can set a global behaviour, or differentiate it according to the user who’s printing. In the example, the global behaviour defines to send the report to client directly (Send to Client), therefore without sending it to the printer. But if user elbati is printing, the report will be sent to the selected printer (Send to Printer).

You can also define a default behaviour associated to the user, in order to establish whether a certain user, when not differently set, wants to send the reports always to a specific printer or not.

After finishing the configuration, you will just have to click on printing button associated to the report (or launch the report by a wizard or whatever) and the system will automatically send the report to the previously set printer.
""",
    'author': 'Agile Business Group & Domsense, Pegueroles SCP, NaN',
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    "depends" : ['base', 'base_calendar'],
    "init_xml" : [],
    "update_xml" : [
        'printing_data.xml',
        'printing_view.xml',
        'wizard/update_printers.xml',
        'security/security.xml',
        ],
    "demo_xml" : [],
    "active": False,
    "installable": True
}
