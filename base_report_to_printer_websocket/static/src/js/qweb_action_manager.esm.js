import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

async function websocketReportActionHandler(action, options, env) {
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
    if (
        !printAction ||
        printAction.backend !== "websocket" ||
        printAction.action !== "server" ||
        printAction.printer_exception
    ) {
        return false;
    }
    const result = await orm.call("ir.actions.report", "print_document_client_action", [
        action.id,
        action.context.active_ids,
        action.data,
    ]);
    if (result) {
        env.services.notification.add(_t("Print job sent via WebSocket!"), {
            type: "success",
        });
        return true;
    }
    env.services.notification.add(_t("Could not send print job!"), {
        type: "danger",
    });
    return false;
}

registry
    .category("ir.actions.report handlers")
    .add("websocket_report_action_handler", websocketReportActionHandler);
