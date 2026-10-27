import {registry} from "@web/core/registry";

export function isSupportedReportType(reportType) {
    return (
        reportType === "qweb-pdf" ||
        reportType.startsWith("qweb-pdf-") ||
        reportType === "qweb-text"
    );
}

async function genericReportActionHandler(action, options, env) {
    const orm = env.services.orm;
    if (!isSupportedReportType(action.report_type)) {
        return false;
    }

    const dispatchers = registry.category("report.print.backends");

    const result = await orm.call(
        "ir.actions.report",
        "print_action_for_report_name",
        [action.report_name],
        {context: env.context}
    );

    if (!result || result.action !== "server") {
        return false;
    }

    const backend = result.backend;

    if (backend && dispatchers.contains(backend)) {
        const dispatcher = dispatchers.get(backend);
        return await dispatcher(action, env);
    }

    return false;
}

registry
    .category("ir.actions.report handlers")
    .add("generic_report_action_handler", genericReportActionHandler, {sequence: 0});
