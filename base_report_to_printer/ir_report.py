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
import os
import base64
from tempfile import mkstemp
import logging
import cups

from openerp.osv import orm, fields
from openerp.tools.config import config

CUPS_HOST = config.get('cups_host', 'localhost')
CUPS_PORT = int(config.get('cups_port', 631))  # config.get returns a string


class report_xml(orm.Model):

    """
    Reports
    """

    def set_print_options(self, cr, uid, report_id, format, context=None):
        """
        Hook to set print options
        """
        options = {}
        if format == 'raw':
            options['raw'] = True
        return options

    def print_direct(self, cr, uid, report_id, result, format, printer,
                     context=None):
        fd, file_name = mkstemp()
        try:
            os.write(fd, base64.decodestring(result))
        finally:
            os.close(fd)
        printer_system_name = ''
        if printer:
            if isinstance(printer, (basestring)):
                printer_system_name = printer
            else:
                printer_system_name = printer.system_name
            connection = cups.Connection(CUPS_HOST, CUPS_PORT)

            options = self.set_print_options(cr, uid, report_id, format,
                                             context=context)

            connection.printFile(printer_system_name, file_name, file_name,
                                 options=options)
            logger = logging.getLogger('base_report_to_printer')
            logger.info("Printing job : '%s'" % file_name)
        return True

    _inherit = 'ir.actions.report.xml'
    _columns = {
        'property_printing_action': fields.property(
            # 'ir.actions.report.xml',
            'printing.action',
            type='many2one',
            relation='printing.action',
            string='Action',
            view_load=True,
            method=True,
        ),
        'printing_printer_id': fields.many2one('printing.printer', 'Printer'),
        'printing_action_ids': fields.one2many(
            'printing.report.xml.action', 'report_id', 'Actions',
            help='This field allows configuring action and printer on a per '
                 'user / company basis'),
    }

    def _get_company_id(self, cr, uid, context=None):
        """
        As it may happend that OpenERP force the uid to 1 to bypass rule (in
        function field), we may sometimes use the company of user
        id 1 instead of the good one. Because we found the real uid and
        company_id in the context in that case, I return this one. It also
        allow other module to give the proper company_id in the context.

        If force_company is in context, use it in prioriy.

        If company_id not in context, take the one from uid.
        """
        if context is None:
            context = {}
        res = context.get('force_company') or context.get('company_id')
        if not res:
            user_obj = self.pool['res.users']
            res = user_obj.read(cr, uid, uid,
                                ['company_id'],
                                context=context)['company_id'][0]
        return res

    def behaviour(self, cr, uid, ids, context=None):
        result = {}
        printer_obj = self.pool['printing.printer']
        printing_act_obj = self.pool['printing.report.xml.action']
        # Set hardcoded default action
        default_action = 'client'
        # Retrieve system wide printer
        default_printer = printer_obj.get_default(cr, uid, context=context)
        if default_printer:
            default_printer = printer_obj.browse(cr, uid, default_printer,
                                                 context=context)

        company_id = self._get_company_id(cr, uid, context)

        # Retrieve user default values
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        if user.printing_action:
            default_action = user.printing_action
        if user.printing_printer_id:
            default_printer = user.printing_printer_id

        for report in self.browse(cr, uid, ids, context):
            action = default_action
            printer = default_printer

            # Retrieve report default values
            if (report.property_printing_action and
                    report.property_printing_action.type != 'user_default'):
                action = report.property_printing_action.type
            if report.printing_printer_id:
                printer = report.printing_printer_id

            # Retrieve report-company specific values
            act_ids = printing_act_obj.search(
                cr, uid,
                [('report_id', '=', report.id),
                 ('user_id', '=', False),
                 ('company_id', '=', company_id),
                 ('action', '!=', 'user_default')], context=context)
            if act_ids:
                company_action = printing_act_obj.behaviour(
                    cr, uid, act_ids[0], context)
                action = company_action['action']
                if company_action['printer']:
                    printer = company_action['printer']

            # Retrieve report-user specific values
            act_ids = printing_act_obj.search(
                cr, uid,
                [('report_id', '=', report.id),
                 ('user_id', '=', uid),
                 ('action', '!=', 'user_default'),
                 '|', ('company_id', '=', company_id),
                 ('company_id', '=', False)], context=context)
            if act_ids:
                user_action = printing_act_obj.behaviour(cr, uid, act_ids[0],
                                                         context)
                action = user_action['action']
                if user_action['printer']:
                    printer = user_action['printer']

            result[report.id] = {
                'action': action,
                'printer': printer,
            }
        return result
