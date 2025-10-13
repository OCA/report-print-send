/* global qz, fetch, console */
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";
import {_t} from "@web/core/l10n/translation";

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

    async printOrDownloadReport(action, env) {
        const report_action = await rpc("/web/dataset/call_kw", {
            model: "ir.actions.report",
            method: "qz_tray_for_report_name",
            args: [[action.report_name]],
            kwargs: {},
        });

        if (report_action && report_action.action === "print") {
            return this._triggerPrint(
                action,
                report_action,
                env?.services?.notification
            );
        }
        return this._triggerDownload(action);
    }

    async _triggerPrint(action, report_action, notificationService) {
        try {
            const data = await rpc("/web/dataset/call_kw", {
                model: "ir.actions.report",
                method: "get_qz_tray_data",
                args: [
                    report_action.id,
                    action.context.active_ids,
                    action.report_type === "qweb-pdf"
                        ? "pdf"
                        : action.report_type === "py3o"
                          ? "py3o"
                          : "text",
                    action.report_name,
                ],
                kwargs: {data: action.data || {}},
                context: action.context || {},
            });

            let printer_name = report_action.printer_name;
            if (printer_name.includes("\\")) {
                const parts = printer_name.split("\\");
                const server = parts[0];
                const printer = parts[1];
                printer_name = printer;
                await qz.websocket.connect({host: server});
            } else {
                await qz.websocket.connect();
            }

            let qz_printer_name = null;
            try {
                qz_printer_name = await qz.printers.find(printer_name);
            } catch {
                if (notificationService) {
                    notificationService.add(_t("Printer not found: " + printer_name), {
                        sticky: true,
                        type: "warning",
                    });
                } else {
                    console.warn("Printer not found:", printer_name);
                }
                try {
                    await qz.websocket.disconnect();
                } catch {
                    /* Ignored */
                }
                return false;
            }

            const config = qz.configs.create(qz_printer_name);
            await qz.print(config, data);
            await qz.websocket.disconnect();

            if (notificationService) {
                notificationService.add(
                    _t("Document sent to the printer: " + qz_printer_name),
                    {sticky: false, type: "info"}
                );
            } else {
                console.info(_t("Document sent to the printer: " + qz_printer_name));
            }

            return true;
        } catch (err) {
            if (notificationService) {
                notificationService.add(
                    _t("Error printing document: " + (err?.message || err)),
                    {sticky: true, type: "danger"}
                );
            } else {
                console.error("Error printing document:", err);
            }
            try {
                await qz.websocket.disconnect();
            } catch {
                /* Ignored */
            }
            return false;
        }
    }

    async _triggerDownload(action) {
        let report_type = "";
        if (action.report_type === "qweb-pdf") {
            report_type = "pdf";
        } else if (action.report_type === "py3o") {
            report_type = "py3o";
        } else {
            report_type = "text";
        }

        return this._downloadReport(action, report_type);
    }

    async _downloadReport(action, report_type) {
        return await rpc("/web/action/load", {
            action_id: action.id,
            report_type: report_type,
        });
    }
}

const handler = new PrintActionHandler();

function print_or_download_report_handler(action, _options, env) {
    return handler.printOrDownloadReport(action, env);
}

registry
    .category("ir.actions.report handlers")
    .add("print_or_download_report", print_or_download_report_handler, {sequence: 0});
