import {PrinterSelectDialog} from "./printer_select_dialog.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

function askPrinter(env, action, printAction) {
    return new Promise((resolve) => {
        env.services.dialog.add(
            PrinterSelectDialog,
            {
                title: action.name
                    ? _t("Print %s on...", action.name)
                    : _t("Select printer"),
                printers: printAction.printers,
                selectedId: printAction.printer_id,
                onSelect: resolve,
            },
            {onClose: () => resolve(undefined)}
        );
    });
}

async function selectReportActionHandler(action, options, env) {
    if (!["qweb-pdf", "qweb-text"].includes(action.report_type)) {
        return false;
    }
    const orm = env.services.orm;
    const printAction = await orm.call(
        "ir.actions.report",
        "print_action_for_report_name",
        [action.report_name],
        {context: {force_print_to_client: action.context.force_print_to_client}}
    );
    if (!printAction || printAction.action !== "select") {
        return false;
    }
    const printers = printAction.printers || [];
    if (!printers.length) {
        env.services.notification.add(
            _t("No printer is available for this report, it will be downloaded."),
            {type: "warning"}
        );
        return false;
    }
    const printerId = await askPrinter(env, action, printAction);
    if (printerId === undefined) {
        return true;
    }
    if (printerId === null) {
        return false;
    }
    const result = await orm.call("ir.actions.report", "print_document_select", [
        action.id,
        action.context.active_ids,
        printerId,
        action.data,
    ]);
    if (result) {
        env.services.notification.add(_t("Successfully sent to printer!"), {
            type: "success",
        });
        return true;
    }
    env.services.notification.add(_t("Could not send to printer!"), {
        type: "danger",
    });
    return false;
}

registry
    .category("ir.actions.report handlers")
    .add("select_report_action_handler", selectReportActionHandler, {sequence: 10});
