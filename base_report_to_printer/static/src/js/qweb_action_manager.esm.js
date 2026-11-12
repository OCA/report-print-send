import {registry} from "@web/core/registry";

const DESTROYED_MESSAGE = "Component is destroyed";

// A server-side print can outlast the component that started it. The
// onClose reload is then refused with "Component is destroyed", which is
// not a print failure; any other error still propagates.
function ignoreDestroyedComponent(options) {
    if (!options || !options.onClose) {
        return;
    }
    const onClose = options.onClose;
    options.onClose = (...args) =>
        Promise.resolve()
            .then(() => onClose(...args))
            .catch((error) => {
                if (error && error.message === DESTROYED_MESSAGE) {
                    return undefined;
                }
                throw error;
            });
}

async function genericReportActionHandler(action, options, env) {
    const orm = env.services.orm;
    if (!["qweb-pdf", "qweb-text"].includes(action.report_type)) {
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
        ignoreDestroyedComponent(options);
        return await dispatcher(action, env);
    }

    return false;
}

registry
    .category("ir.actions.report handlers")
    .add("generic_report_action_handler", genericReportActionHandler, {sequence: 0});
