import {registry} from "@web/core/registry";

async function genericReportActionHandler(action, options, env) {
    if (action.report_type !== "qweb-pdf") {
        return false;
    }

    const dispatchers = registry.category("report.print.backends");

    const backend = action.context?.print_backend;
    if (backend && dispatchers.contains(backend)) {
        const dispatcher = dispatchers.get(backend);
        return await dispatcher(action, env);
    }

    return false;
}

registry
    .category("ir.actions.report handlers")
    .add("generic_report_action_handler", genericReportActionHandler, {sequence: 0});
