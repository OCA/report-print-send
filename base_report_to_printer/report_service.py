# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
#    Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
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

import openerp

from openerp.service.report import self_reports

original_exp_report = openerp.service.report.exp_report


def exp_report(db, uid, object, ids, datas=None, context=None):
    """ Export Report """
    # We can't use the named args because a monkey patch in 'calendar'
    # doesn't use them and use a different name for 'datas'
    res = original_exp_report(db, uid, object, ids, datas, context)
    self_reports[res]['report_name'] = object
    return res


openerp.service.report.exp_report = exp_report


original_exp_report_get = openerp.service.report.exp_report_get


def exp_report_get(db, uid, report_id):
    registry = openerp.registry(db)
    cr = registry.cursor()
    try:
        # First of all load report defaults: name, action and printer
        report_obj = registry['ir.actions.report.xml']
        report_name = self_reports[report_id]['report_name']
        report = report_obj.search(cr, uid,
                                   [('report_name', '=', report_name)])
        if report:
            report = report_obj.browse(cr, uid, report[0])
            data = report.behaviour()[report.id]
            action = data['action']
            printer = data['printer']
            if action != 'client':
                if (self_reports and self_reports.get(report_id)
                        and self_reports[report_id].get('result')
                        and self_reports[report_id].get('format')):
                    printer.print_document(report,
                                           self_reports[report_id]['result'],
                                           self_reports[report_id]['format'])
                    # FIXME "Warning" removed as it breaks the workflow
                    # it would be interesting to have a dialog box to
                    # confirm if we really want to print in this case it
                    # must be with a by pass parameter to allow massive
                    # prints
                    # raise osv.except_osv(
                    #     _('Printing...'),
                    #     _('Document sent to printer %s') % (printer,))

    except:
        cr.rollback()
        raise
    finally:
        cr.close()

    return original_exp_report_get(db, uid, report_id)


openerp.service.report.exp_report_get = exp_report_get
