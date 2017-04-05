# -*- coding: utf-8 -*-
# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo

from odoo.service.report import self_reports

original_exp_report = odoo.service.report.exp_report


def exp_report(db, uid, object, ids, datas=None, context=None):
    """ Export Report """
    # We can't use the named args because a monkey patch in 'calendar'
    # doesn't use them and use a different name for 'datas'
    res = original_exp_report(db, uid, object, ids, datas, context)
    self_reports[res]['report_name'] = object
    return res


odoo.service.report.exp_report = exp_report


original_exp_report_get = odoo.service.report.exp_report_get


def exp_report_get(db, uid, report_id):
    # First we need to know if the module is installed
    registry = odoo.registry(db)
    if registry.get('printing.printer'):
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
                    if all(self_reports,
                           self_reports.get(report_id),
                           self_reports[report_id].get('result'),
                           self_reports[report_id].get('format')
                           ):
                        printer.print_document(report,
                                               self_reports
                                               [report_id]['result'],
                                               self_reports
                                               [report_id]['format'])
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


odoo.service.report.exp_report_get = exp_report_get
