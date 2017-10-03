odoo.define('base_report_to_printer.print', function(require) {
    'use strict';

    var ActionManager = require('web.ActionManager');
    var core = require('web.core');
    var framework = require('web.framework');
    var Model = require('web.Model');

    ActionManager.include({
        ir_actions_report: function(action, options) {
            action_val = _.clone(action);
            var _t = core._t;
            var self = this;
            var _super = this._super;

            if ('report_type' in action_val && action_val.report_type === 'qweb-pdf') {
                framework.blockUI();
                new Model('ir.actions.report').
                    call('print_action_for_report_name', [action_val.report_name]).
                    then(function(print_action){
                        if (print_action && print_action.action_val === 'server') {
                            framework.unblockUI();
                            new Model('report').
                                call('print_document',
                                      [action_val.context.active_ids, action_val.report_name],
                                      {data: action_val.data || {}, context: action_val.context || {}}).
                                then(function(){
                                    self.do_notify(_t('Report'),
                                                   _t('Document sent to the printer ') + print_action.printer_name);
                                }).fail(function() {
                                    self.do_notify(_t('Report'),
                                                   _t('Error when sending the document to the printer ') + print_action.printer_name);

                                });
                        } else {
                            return _super.apply(self, [action_val, options]);
                        }
                    });
            } else {
                return _super.apply(self, [action_val, options]);
            }
        }
    });
});
