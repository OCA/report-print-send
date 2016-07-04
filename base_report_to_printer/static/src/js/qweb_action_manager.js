odoo.define('base_report_to_printer.print', function(require) {
    'use strict';

    var ActionManager = require('web.ActionManager');
    var core = require('web.core');
    var framework = require('web.framework');
    var Model = require('web.Model');

    ActionManager.include({
        ir_actions_report_xml: function(action, options) {
            framework.blockUI();
            action = _.clone(action);
            var _t = core._t;
            var self = this;
            var _super = this._super;

            if ('report_type' in action && action.report_type === 'qweb-pdf') {
                new Model('ir.actions.report.xml')
                    .call('print_action_for_report_name', [action.report_name])
                    .then(function(print_action){
                        if (print_action && print_action.action === 'server') {
                            framework.unblockUI();
                            new Model('report')
                                .call('print_document',
                                      [action.context.active_ids,
                                       action.report_name,
                                       ],
                                      {data: action.data || {},
                                       context: action.context || {},
                                       })
                                .then(function(){
                                    self.do_notify(_t('Report'),
                                                   _t('Document sent to the printer ') + print_action.printer_name);
                                }).fail(function() {
                                    self.do_notify(_t('Report'),
                                                   _t('Error when sending the document to the printer ') + print_action.printer_name);

                                });
                        } else {
                            return _super.apply(self, [action, options]);
                        }
                    });
            } else {
                return _super.apply(self, [action, options]);
            }
        }
    });
    
});

