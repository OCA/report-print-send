/** @odoo-module */
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

async function cupsReportActionHandler(action, options, env) {
    if (action.report_type === "qweb-pdf") {
        const orm = env.services.orm;

        const print_action = await orm.call(
            "ir.actions.report",
            "print_action_for_report_name",
            [action.report_name]
        );
        if (print_action && print_action.action === "server") {
            const result = await orm.call("ir.actions.report", "print_document", [
                action.id,
                action.context.active_ids,
                action.data,
            ]);
            if (result) {
                env.services.notification.add(_t("Successfully sent to printer!"));
            } else {
                env.services.notification.add(_t("Could not send to printer!"));
            }
            return true;
        }
    }
}

registry
    .category("ir.actions.report handlers")
    .add("cups_report_action_handler", cupsReportActionHandler);
