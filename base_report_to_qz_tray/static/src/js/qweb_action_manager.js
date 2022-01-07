qz.security.setCertificatePromise(function (resolve, reject) {
    fetch("/qz-certificate", {
        cache: "no-store",
        headers: {"Content-Type": "text/plain"},
    }).then(function (data) {
        data.ok ? resolve(data.text()) : reject(data.text());
    });
});
qz.security.setSignatureAlgorithm("SHA512");
qz.security.setSignaturePromise(function (toSign) {
    return function (resolve, reject) {
        fetch("/qz-sign-message?request=" + toSign, {
            cache: "no-store",
            headers: {"Content-Type": "text/plain"},
        }).then(function (data) {
            data.ok ? resolve(data.text()) : reject(data.text());
        });
    };
});

odoo.define("base_report_to_qz_tray.print", function (require) {
    "use strict";

    var ActionManager = require("web.ActionManager");
    var core = require("web.core");
    var _t = core._t;

    ActionManager.include({
        _triggerDownload: function (action, options, type) {
            var self = this;
            var _super = this._super;
            if (type === "pdf" || type === "text") {
                self._rpc({
                    model: "ir.actions.report",
                    method: "qz_tray_for_report_name",
                    args: [action.report_name],
                }).then(function (report_action) {
                    if (report_action && report_action.action === "print") {
                        self._rpc({
                            model: "ir.actions.report",
                            method: "get_qz_tray_data",
                            args: [report_action.id, action.context.active_ids, type],
                            kwargs: {data: action.data || {}},
                            context: action.context || {},
                        }).then(function (data) {
                            qz.websocket
                                .connect()
                                .then(function () {
                                    return qz.printers.find(report_action.printer_name);
                                })
                                .then(function (printer_name) {
                                    var config = qz.configs.create(printer_name);
                                    return qz.print(config, data);
                                })
                                .then(qz.websocket.disconnect)
                                .then(function () {
                                    self.do_notify(
                                        _t("Report"),
                                        _.str.sprintf(
                                            _t("Document sent to the printer %s"),
                                            print_action.printer_name
                                        )
                                    );
                                })
                                .catch(function (err) {
                                    console.log(err);
                                    return _super.apply(self, [action, options, type]);
                                });
                        });
                    } else {
                        return _super.apply(self, [action, options, type]);
                    }
                });
            } else {
                return _super.apply(self, [action, options, type]);
            }
        },
    });
});
