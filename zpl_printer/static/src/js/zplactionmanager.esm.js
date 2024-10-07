/** @odoo-module **/

import {browser} from "@web/core/browser/browser";
import {makeErrorFromResponse} from "@web/core/network/rpc_service";
import {registry} from "@web/core/registry";

async function print(zpl, url) {
    try {
        browser.fetch(url, {
            method: "POST",
            body: zpl,
        });
    } catch (e) {
        // Generally ignore errors here, as it is probably just a CORS error, that can be ignored,
        // if the label has been successfully printed.
        console.log(e);
    }
}

async function get_zpl_data(options) {
    const xhr = new browser.XMLHttpRequest();
    let data = new FormData();
    if (Object.prototype.hasOwnProperty.call(options, "form")) {
        xhr.open(options.form.method, options.form.action);
        data = new FormData(options.form);
    } else {
        xhr.open("POST", options.url);
        Object.entries(options.data).forEach((entry) => {
            const [key, value] = entry;
            data.append(key, value);
        });
    }
    data.append("token", "dummy-because-api-expects-one");
    if (odoo.csrf_token) {
        data.append("csrf_token", odoo.csrf_token);
    }
    xhr.onload = () => {
        // In Odoo, the default mimetype, including for JSON errors is text/html (ref: http.py:Root.get_response )
        // in that case, in order to also be able to download html files, we check if we get a proper filename to be able to download
        if (xhr.status === 200) {
            if (xhr.response.includes("^XA")) {
                print(xhr.response, options.printer_url);
                return xhr.response;
            }
            console.log("Response does not contain zpl data", xhr.response);
        } else {
            const decoder = new FileReader();
            decoder.onload = () => {
                const contents = decoder.result;
                const doc = new DOMParser().parseFromString(contents, "text/html");
                const nodes =
                    doc.body.children.length === 0
                        ? doc.body.childNodes
                        : doc.body.children;

                const error = {};
                try {
                    // A Serialized python Error
                    const node = nodes[1] || nodes[0];
                    console.log(JSON.parse(node.textContent));
                } catch {
                    console.log({
                        message: "Arbitrary Uncaught Python Exception",
                        data: {
                            debug:
                                `${xhr.status}` +
                                `\n` +
                                `${nodes.length > 0 ? nodes[0].textContent : ""}
                                ${nodes.length > 1 ? nodes[1].textContent : ""}`,
                        },
                    });
                }
                console.log(makeErrorFromResponse(error));
            };
            decoder.readAsText(xhr.response);
        }
    };
    xhr.send(data);
}

registry
    .category("ir.actions.report handlers")
    .add("zpl_handler", async function (action, options, env) {
        // Zpl reports
        if ("report_type" in action && action.report_type === "qweb-zpl") {
            let url = `/report/zpl/${action.report_name}`;
            const actionContext = action.context || {};
            if (
                _.isUndefined(action.data) ||
                _.isNull(action.data) ||
                (_.isObject(action.data) && _.isEmpty(action.data))
            ) {
                // Build a query string with `action.data` (it's the place where reports
                // using a wizard to customize the output traditionally put their options)
                if (actionContext.active_ids) {
                    var activeIDsPath = "/" + actionContext.active_ids.join(",");
                    url += activeIDsPath;
                }
            } else {
                var serializedOptionsPath =
                    "?options=" + encodeURIComponent(JSON.stringify(action.data));
                serializedOptionsPath +=
                    "&context=" + encodeURIComponent(JSON.stringify(actionContext));
                url += serializedOptionsPath;
            }
            env.services.ui.block();
            try {
                const printer_data = await env.services.rpc("/web/dataset/call_kw", {
                    model: "zpl_printer.zpl_printer",
                    method: "get_label_printer_data",
                    args: [[], action.report_name, actionContext.active_ids],
                    kwargs: {},
                });
                await get_zpl_data({
                    url: "/report/download",
                    data: {
                        data: JSON.stringify([
                            url,
                            action.report_type,
                            printer_data.resolution,
                        ]),
                        context: JSON.stringify(env.services.user.context),
                    },
                    printer_url: printer_data.url,
                });
            } finally {
                env.services.ui.unblock();
            }
            const onClose = options.onClose;
            if (action.close_on_report_download) {
                return env.services.action.doAction(
                    {type: "ir.actions.act_window_close"},
                    {onClose}
                );
            } else if (onClose) {
                onClose();
            }
            return Promise.resolve(true);
        }
        return Promise.resolve(false);
    });
