odoo.define("base_report_to_printer.print", function (require) {
    "use strict";

    var ActionManager = require("web.ActionManager");
    var core = require("web.core");
    var _t = core._t;

    ActionManager.include({
        _triggerDownload: function (action, options, type) {
            var self = this;
            var _super = this._super;
            if (type === "pdf" || "text") {
                this._rpc({
                    model: "ir.actions.report",
                    method: "print_action_for_report_name",
                    args: [action.report_name],
                }).then(function (print_action) {
                    if (print_action && print_action.action === "server") {
                        self._rpc({
                            model: "ir.actions.report",
                            method: "print_document",
                            args: [action.id, action.context.active_ids],
                            kwargs: {data: action.data || {}},
                            context: action.context || {},
                        }).then(
                            function () {
                                self.do_notify(
                                    _t("Report"),
                                    _.str.sprintf(
                                        _t("Document sent to the printer %s"),
                                        print_action.printer_name
                                    )
                                );
                                if (action.close_on_report_download) {
                                    var closeAction = {
                                        type: "ir.actions.act_window_close",
                                    };
                                    self.doAction(
                                        closeAction,
                                        _.pick(options, "on_close")
                                    );
                                } else {
                                    options.on_close();
                                }
                            },
                            function () {
                                self.do_notify(
                                    _t("Report"),
                                    _.str.sprintf(
                                        _t(
                                            "Error when sending the document " +
                                                "to the printer "
                                        ),
                                        print_action.printer_name
                                    )
                                );
                                if (action.close_on_report_download) {
                                    var closeAction = {
                                        type: "ir.actions.act_window_close",
                                    };
                                    self.doAction(
                                        closeAction,
                                        _.pick(options, "on_close")
                                    );
                                } else {
                                    options.on_close();
                                }
                            }
                        );
                    } else {
                        return _super.apply(self, [action, options, type]);
                    }
                });
                return Promise.reject();
            }
            return _super.apply(self, [action, options, type]);
        },
    });
});
