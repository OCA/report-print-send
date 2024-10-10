/** @odoo-module **/
/* global qz */

import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export default class PrintActionHandler {
    constructor() {
        qz.security.setCertificatePromise((resolve, reject) => {
            fetch("/qz-certificate", {
                cache: "no-store",
                headers: {"Content-Type": "text/plain"},
            })
                .then((response) =>
                    response
                        .text()
                        .then((text) => (response.ok ? resolve(text) : reject(text)))
                )
                .catch(reject);
        });
        qz.security.setSignatureAlgorithm("SHA512");
        qz.security.setSignaturePromise((toSign) => (resolve, reject) => {
            fetch(`/qz-sign-message?request=${toSign}`, {
                cache: "no-store",
                headers: {"Content-Type": "text/plain"},
            })
                .then((response) =>
                    response
                        .text()
                        .then((text) => (response.ok ? resolve(text) : reject(text)))
                )
                .catch(reject);
        });
    }

    async printOrDownloadReport(action, options, env) {
        if (action.report_type === "qweb-pdf") {
            return this._triggerDownload(action, options, "pdf", env);
        } else if (
            action.report_type === "qweb-text" ||
            action.report_type === "py3o"
        ) {
            const report_type = action.report_type === "py3o" ? "py3o" : "text";
            return this._triggerDownload(action, options, report_type, env);
        }
    }

    async _triggerDownload(action, options, report_type, env) {
        try {
            env.services.ui.block();
            const report_action = await env.services.rpc("/web/dataset/call_kw", {
                model: "ir.actions.report",
                method: "qz_tray_for_report_name",
                args: [[action.report_name]],
                kwargs: {},
            });
            if (report_action && report_action.action === "print") {
                env.services.ui.unblock();
                const data = await env.services.rpc("/web/dataset/call_kw", {
                    model: "ir.actions.report",
                    method: "get_qz_tray_data",
                    args: [
                        report_action.id,
                        action.context.active_ids,
                        report_type,
                        action.report_name,
                    ],
                    kwargs: {data: action.data || {}},
                    context: action.context || {},
                });
                // CM-Test: If printer name contains an IP, split and use
                var printer_name = report_action.printer_name;
                if (printer_name.includes("\\")) {
                    var parts = printer_name.split("\\");
                    var server = parts[0];
                    var printer = parts[1];
                    printer_name = printer;
                    await qz.websocket.connect({host: server});
                } else {
                    await qz.websocket.connect();
                }
                const qz_printer_name = await qz.printers.find(printer_name);
                const config = qz.configs.create(qz_printer_name);
                await qz.print(config, data);
                await qz.websocket.disconnect();
                env.services.notification.add(
                    _t("Document sent to the printer: " + qz_printer_name),
                    {sticky: true, type: "info"}
                );
                // Cancel PDF download
                return true;
            }
            env.services.ui.unblock();
        } catch (err) {
            env.services.ui.unblock();
            console.log(err);
        }
    }
}

const handler = new PrintActionHandler();

function print_or_download_report_handler(action, options, env) {
    return handler.printOrDownloadReport(action, options, env);
}

registry
    .category("ir.actions.report handlers")
    .add("print_or_download_report", print_or_download_report_handler, {sequence: 0});
