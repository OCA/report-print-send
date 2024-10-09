/** @odoo-module */
import {registry} from "@web/core/registry";

async function cupsReportActionHandler(action, options, env) {
    if (action.report_type === "qweb-pdf") {
        const orm = env.services.orm;

        const print_action = await orm.call(
            "ir.actions.report",
            "print_action_for_report_name",
            [action.report_name]
        );
        if (
            print_action &&
            print_action.action === "server" &&
            !print_action.printer_exception
        ) {
            const result = await orm.call("ir.actions.report", "print_document", [
                action.id,
                action.context.active_ids,
                action.data,
            ]);
            if (result) {
                env.services.notification.add(env._t("Successfully sent to printer!"), {
                    type: "success",
                });
            } else {
                env.services.notification.add(env._t("Could not send to printer!"), {
                    type: "danger",
                });
            }
            return true;
        }
        if (print_action.printer_exception) {
            env.services.notification.add(
                env._t("The printer couldn't be reached. Downloading document instead"),
                {
                    type: "warning",
                }
            );
        }
    }
}

registry
    .category("ir.actions.report handlers")
    .add("cups_report_action_handler", cupsReportActionHandler);
