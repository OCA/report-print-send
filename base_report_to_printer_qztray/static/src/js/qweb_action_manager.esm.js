/* global qz */
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

async function QZPrintDispatcher(action, env) {
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
    const orm = env.services.orm;

    const print_action = await orm.call(
        "ir.actions.report",
        "print_action_for_report_name",
        [action.report_name],
        {context: {force_print_to_client: action.context.force_print_to_client}}
    );

    if (!print_action || print_action.action !== "server") {
        return false;
    }
    const printer_backend = print_action.backend;
    if (printer_backend !== "qztray") {
        return false;
    }

    const notification = env.services.notification;

    try {
        const data = await rpc("/web/dataset/call_kw", {
            model: "ir.actions.report",
            method: "get_qz_tray_data",
            args: [
                print_action.id,
                action.context.active_ids,
                "pdf",
                action.report_name,
            ],
            kwargs: {data: action.data || {}},
            context: action.context,
        });

        let printerName = print_action.printer_name;

        if (printerName.includes("\\")) {
            const [host, printer] = printerName.split("\\");
            printerName = printer;
            await qz.websocket.connect({host});
        } else {
            await qz.websocket.connect();
        }

        const qzPrinter = await qz.printers.find(printerName);
        const config = qz.configs.create(qzPrinter);

        await qz.print(config, data);
        await qz.websocket.disconnect();

        notification.add(_t("Document sent to QZ Tray printer: %s", printerName), {
            type: "success",
        });

        return true;
    } catch (err) {
        try {
            await qz.websocket.disconnect();
        } catch {
            /* Ignore */
        }

        notification.add(
            _t("Error printing document via QZ Tray: %s", err?.message || err),
            {type: "danger", sticky: true}
        );

        return false;
    }
}

registry.category("report.print.backends").add("qztray", QZPrintDispatcher);
