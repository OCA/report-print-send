import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

async function websocketDispatcher(action, env) {
    const orm = env.services.orm;

    const print_action = await orm.call(
        "ir.actions.report",
        "print_action_for_report_name",
        [action.report_name],
        {context: {force_print_to_client: action.context.force_print_to_client}}
    );

    if (print_action && print_action.action === "server") {
        const result = await orm.call(
            "ir.actions.report",
            "print_document_client_action",
            [action.id, action.context.active_ids, action.data]
        );
        if (result) {
            env.services.notification.add(_t("Print job sent via WebSocket!"), {
                type: "success",
            });
            return true;
        }
        env.services.notification.add(_t("Could not send print job!"), {
            type: "danger",
        });
    }
    return false;
}

registry.category("report.print.backends").add("websocket", websocketDispatcher);
