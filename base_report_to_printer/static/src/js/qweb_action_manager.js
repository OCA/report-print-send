odoo.define('base_report_to_printer.print', function(require) {
    'use strict';

    var ActionManager = require('web.ActionManager');
    var core = require('web.core');
    var framework = require('web.framework');
    var Model = require('web.Model');

    ActionManager.include({
        ir_actions_report_xml: function(action, options) {
            var _action = _.clone(action);
            var _t = core._t;
            var self = this;
            var _super = this._super;

            if ('report_type' in _action && _action.report_type === 'qweb-pdf') {
                framework.blockUI();
                new Model('ir.actions.report.xml')
                    .call('print_action_for_report_name', [_action.report_name])
                    .then(function(print_action){
                        if (print_action && print_action.action === 'server') {
                            framework.unblockUI();
                            new Model('report')
                                .call('print_document',
                                      [_action.context.active_ids,
                                       _action.report_name,
                                       ],
                                      {data: _action.data || {},
                                       context: _action.context || {},
                                       })
                                .then(function(){
                                    self.do_notify(_t('Report'),
                                                   _t('Document sent to the printer ') + print_action.printer_name);
                                }).fail(function() {
                                    self.do_notify(_t('Report'),
                                                   _t('Error when sending the document to the printer ') + print_action.printer_name);

                                });
                        } else {
                            return _super.apply(self, [_action, options]);
                        }
                    });
            } else {
                return _super.apply(self, [_action, options]);
            }
        }
    });
});
