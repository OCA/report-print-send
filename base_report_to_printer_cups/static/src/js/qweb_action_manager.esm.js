import {_t} from "@web/core/l10n/translation";
import {markup} from "@odoo/owl";
import {registry} from "@web/core/registry";

async function cupsDispatcher(action, env) {
    const orm = env.services.orm;

    const print_action = await orm.call(
        "ir.actions.report",
        "print_action_for_report_name",
        [action.report_name],
        {context: {force_print_to_client: action.context.force_print_to_client}}
    );

    let printer_exception = print_action.printer_exception;
    if (print_action && print_action.action === "server" && !printer_exception) {
        const result = await orm.call(
            "ir.actions.report",
            "print_document_client_action",
            [action.id, action.context.active_ids, action.data]
        );
        if (result) {
            env.services.notification.add(_t("Successfully sent to CUPS printer!"), {
                type: "success",
            });
            return true;
        }
        env.services.notification.add(_t("Could not send to printer!"), {
            type: "danger",
        });
        printer_exception = true;
    }
    if (print_action && print_action.action === "server" && printer_exception) {
        const terms = {
            the_report: _t("The report"),
            couldnt_be_printed: _t(
                "couldn't be printed. Click on the button below to download it"
            ),
            issue_on: _t("Issue on"),
        };
        const notificationRemove = env.services.notification.add(
            markup(
                `<p>${terms.the_report} <strong>${action.name}</strong> ${terms.couldnt_be_printed}</p>`
            ),
            {
                title: `${terms.issue_on} ${print_action.printer_name}`,
                type: "warning",
                sticky: true,
                buttons: [
                    {
                        name: _t("Print"),
                        primary: true,
                        icon: "fa-print",
                        onClick: async () => {
                            const context = {
                                force_print_to_client: true,
                                must_skip_send_to_printer: true,
                            };
                            env.services.user.updateContext(context);
                            await env.services.action.doAction(
                                {type: "ir.actions.report", ...action},
                                {
                                    additionalContext: context,
                                }
                            );
                            notificationRemove();
                        },
                    },
                ],
            }
        );
        return true;
    }
    return false;
}

registry.category("report.print.backends").add("cups", cupsDispatcher);
