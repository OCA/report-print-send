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

import os
import base64
import threading
from tempfile import mkstemp

import cups
import thread
from threading import Thread
from threading import Lock

import netsvc
import tools
import time 
from osv import fields
from osv import osv
import pooler 
import tools
from tools.translate import _
from base_calendar import base_calendar
import logging


#
#  Printers
#
class printing_printer(osv.osv):
    _name = "printing.printer"
    _description = "Printer"

    _columns = {
        'name' : fields.char('Name',size=64,required=True,select="1"),
        'system_name': fields.char('System Name',size=64,required=True,select="1"),
        'default':fields.boolean('Default Printer',required=True,readonly=True),
        'status': fields.selection([('unavailable','Unavailable'),('printing','Printing'),('unknown','Unknown'),('available','Available'),('error','Error'),('server-error','Server Error')], 'Status', required=True, readonly=True),
        'status_message': fields.char('Status Message', size=500, readonly=True),
        'model': fields.char('Model', size=500, readonly=True),
        'location': fields.char('Location', size=500, readonly=True),
        'uri': fields.char('URI', size=500, readonly=True),
    }
    _order = "name"
    
    _defaults = {
        'default': lambda *a: False,
        'status': lambda *a: 'unknown',
    }

    def __init__(self, pool, cr):
        super(printing_printer, self).__init__(pool, cr)
        self.lock = Lock()
        self.last_update = None
        self.updating = False

    def update_printers_status(self, db_name, uid, context):
        db, pool = pooler.get_db_and_pool(db_name)
        cr = db.cursor()

        try:
            connection = cups.Connection()
            printers = connection.getPrinters()
            server_error = False
        except:
            server_error = True

        mapping = {
            3 : 'available',
            4 : 'printing',
            5 : 'error'
        }
        
        try:
        # Skip update to avoid the thread being created again
            ctx = context.copy()
            ctx['skip_update'] = True
            ids = self.pool.get('printing.printer').search(cr, uid, [], context=ctx)
            for printer in self.pool.get('printing.printer').browse(cr, uid, ids, context=ctx):
                vals = {}
                if server_error:
                    status = 'server-error'
                elif printer.system_name in printers:
                    info = printers[printer.system_name]
                    status = mapping.get( info['printer-state'], 'unknown' )
                    vals = {
                        'model': info.get('printer-make-and-model', False),
                        'location': info.get('printer-location', False),
                        'uri': info.get('device-uri', False),
                    }
                else:
                    status = 'unavailable'

                vals['status'] = status
                self.pool.get('printing.printer').write(cr, uid, [printer.id], vals, context)
            cr.commit()
        except:
            cr.rollback()
            raise
        finally:
            cr.close()
        with self.lock:
            self.updating = False
            self.last_update = time.time()


    def start_printer_update(self, cr, uid, context):
        self.lock.acquire()
        if self.updating:
            self.lock.release()
            return
        self.updating = True
        self.lock.release()
        thread = Thread(target=self.update_printers_status, args=(cr.dbname, uid, context.copy()))
        thread.start()

    def update(self, cr, uid, context=None):
        if not context or context.get('skip_update'):
            return
        self.lock.acquire()
        last_update = self.last_update
        updating = self.updating
        self.lock.release()
        now = time.time()
        # Only update printer status if current status is more than 10 seconds old.
        if not last_update or now - last_update > 10:
            self.start_printer_update(cr, uid, context)
            # Wait up to five seconds for printer status update
            for x in range(0,5):
                time.sleep(1)
                self.lock.acquire()
                updating = self.updating
                self.lock.release()
                if not updating:
                    break
        return True

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        self.update(cr, uid, context)
        return super(printing_printer,self).search(cr, uid, args, offset, limit, order, context, count)

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        self.update(cr, uid, context)
        return super(printing_printer,self).read(cr, uid, ids, fields, context, load)

    def browse(self, cr, uid, ids, context=None):
        self.update(cr, uid, context)
        return super(printing_printer,self).browse(cr, uid, ids, context)

    def set_default(self, cr, uid, ids, context):
        if not ids:
            return
        default_ids= self.search(cr, uid,[('default','=',True)])
        self.write(cr, uid, default_ids, {'default':False}, context)
        self.write(cr, uid, ids[0], {'default':True}, context)
        return True
    
    def get_default(self,cr,uid,context):
        printer_ids = self.search(cr, uid,[('default','=',True)])
        if printer_ids:
            return printer_ids[0]
        return False

printing_printer()



#
# Actions
#

def _available_action_types(self, cr, uid, context=None):
    return [
        ('server',_('Send to Printer')),
        ('client',_('Send to Client')),
        ('user_default',_("Use user's defaults")),
    ]

class printing_action(osv.osv):
    _name = 'printing.action'
    _description = 'Print Job Action'

    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'type': fields.selection(_available_action_types, 'Type', required=True),
    }
printing_action()

# 
# Users
#

class res_users(osv.osv):
    _name = "res.users"
    _inherit = "res.users"

    def _user_available_action_types(self, cr, uid, context=None):
        if context is None:
            context={}
        return [x for x in _available_action_types(self, cr, uid, context) if x[0] != 'user_default']

    _columns = {
        'printing_action': fields.selection(_user_available_action_types, 'Printing Action'),
        'printing_printer_id': fields.many2one('printing.printer', 'Default Printer'),
    }

res_users()

#
# Reports
#    

class report_xml(osv.osv):

    def print_direct(self, cr, uid, result, format, printer):
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
            if format == 'raw':
                # -l is the same as -o raw
                cmd = "lpr -l -P %s %s" % (printer_system_name,file_name)
            else:
                cmd = "lpr -P %s %s" % (printer_system_name,file_name)
            logger = logging.getLogger('base_report_to_printer')
            logger.info("Printing job : '%s'" % cmd)
            os.system(cmd)
        return True

    _inherit = 'ir.actions.report.xml'
    _columns = {
        'property_printing_action': fields.property(
            #'ir.actions.report.xml',
            'printing.action',
            type='many2one',
            relation='printing.action',
            string='Action',
            view_load=True,
            method=True,
        ),
        'printing_printer_id': fields.many2one('printing.printer', 'Printer'),
        'printing_action_ids': fields.one2many('printing.report.xml.action', 'report_id', 'Actions', help='This field allows configuring action and printer on a per user basis'),
    }

    def behaviour(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        result = {}

        # Set hardcoded default action
        default_action = 'client'
        # Retrieve system wide printer
        default_printer = self.pool.get('printing.printer').get_default(cr,uid,context)
        if default_printer:
            default_printer = self.pool.get('printing.printer').browse(cr,uid,default_printer,context).system_name


        # Retrieve user default values
        user = self.pool.get('res.users').browse(cr, uid, context)
        if user.printing_action:
            default_action = user.printing_action
        if user.printing_printer_id:
            default_printer = user.printing_printer_id.system_name

        for report in self.browse(cr, uid, ids, context):
            action = default_action
            printer = default_printer

            # Retrieve report default values
            if report.property_printing_action and report.property_printing_action.type != 'user_default':
                action = report.property_printing_action.type
            if report.printing_printer_id:
                printer = report.printing_printer_id

            # Retrieve report-user specific values
            user_action = self.pool.get('printing.report.xml.action').behaviour(cr, uid, report.id, context)
            if user_action and user_action['action'] != 'user_default':
                action = user_action['action']
                if user_action['printer']:
                    printer = user_action['printer']

            result[report.id] = {
                'action': action,
                'printer': printer,
            }
        return result


report_xml()

class report_xml_action(osv.osv):
    _name = 'printing.report.xml.action'
    _description = 'Report Printing Actions'
    _columns = {
        'report_id': fields.many2one('ir.actions.report.xml', 'Report', required=True, ondelete='cascade'),
        'user_id': fields.many2one('res.users', 'User', required=True, ondelete='cascade'),
        'action': fields.selection(_available_action_types, 'Action', required=True),
        'printer_id': fields.many2one('printing.printer', 'Printer'),
    }

    def behaviour(self, cr, uid, report_id, context=None):
        if context is None:
            context={}
        result = {}
        ids = self.search(cr, uid, [('report_id','=',report_id),('user_id','=',uid)], context=context)
        if not ids:
            return False
        action = self.browse(cr, uid, ids[0], context)
        return {
            'action': action.action,
            'printer': action.printer_id.system_name,
        }
report_xml_action()

class virtual_report_spool(base_calendar.virtual_report_spool):

    def exp_report(self, db, uid, object, ids, datas=None, context=None):
        res = super(virtual_report_spool, self).exp_report(db, uid, object, ids, datas, context)
        self._reports[res]['report_name'] = object
        return res

    def exp_report_get(self, db, uid, report_id):

        cr = pooler.get_db(db).cursor()
        try:
            pool = pooler.get_pool(cr.dbname)
            # First of all load report defaults: name, action and printer
            report_obj = pool.get('ir.actions.report.xml')
            report = report_obj.search(cr,uid,[('report_name','=',self._reports[report_id]['report_name'])])
            if report:
                report = report_obj.browse(cr,uid,report[0])
                name = report.name
                data = report.behaviour()[report.id]
                action = data['action']
                printer = data['printer']
                if action != 'client':
                    if (self._reports and self._reports.get(report_id, False) and self._reports[report_id].get('result', False)
                        and self._reports[report_id].get('format', False)):
                        report_obj.print_direct(cr, uid, base64.encodestring(self._reports[report_id]['result']),
                            self._reports[report_id]['format'], printer)
        except:
            cr.rollback()
            raise
        finally:
            cr.close()

        res = super(virtual_report_spool, self).exp_report_get(db, uid, report_id)
        return res

virtual_report_spool()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
