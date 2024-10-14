import {markup} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

async function cupsReportActionHandler(action, options, env) {
    if (action.report_type === "qweb-pdf") {
        const orm = env.services.orm;

        const print_action = await orm.call(
            "ir.actions.report",
            "print_action_for_report_name",
            [action.report_name],
            {context: {force_print_to_client: action.context.force_print_to_client}}
        );
        var printer_exception = print_action.printer_exception;
        if (print_action && print_action.action === "server" && !printer_exception) {
            // The Odoo CUPS backend is ok. We try to print into the printer
            const result = await orm.call(
                "ir.actions.report",
                "print_document_client_action",
                [action.id, action.context.active_ids, action.data]
            );
            if (result) {
                env.services.notification.add(_t("Successfully sent to printer!"), {
                    type: "success",
                });
                return true;
                // In case of exception during the job, we won't get any response. So we
                // should flag the exception and notify the user
            }
            env.services.notification.add(_t("Could not sent to printer!"), {
                type: "danger",
            });
            printer_exception = true;
        }
        if (print_action && print_action.action === "server" && printer_exception) {
            // Just so the translation engine detects them as it doesn't do it inside
            // template strings
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
                    messageIsHtml: true,
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
    }
}

registry
    .category("ir.actions.report handlers")
    .add("cups_report_action_handler", cupsReportActionHandler);
