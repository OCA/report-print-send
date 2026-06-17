/* @odoo-module */
/* Copyright 2025 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {Component, onWillStart} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {user} from "@web/core/user";
import {useService} from "@web/core/utils/hooks";

export class SelectPrinterMenu extends Component {
    setup() {
        this.action = useService("action");
        onWillStart(async () => {
            this.isPrinterUser = await user.hasGroup(
                "base_report_to_printer.printer_button_group"
            );
        });
    }

    /**
     * Go to user init action when clicking it
     * @private
     */
    onClickSelectPrinter() {
        this.action.doAction(
            "base_report_to_printer.action_user_default_printer_selector"
        );
    }
}

SelectPrinterMenu.template = "base_report_to_printer.PrinterSelectorButton";

export const systrayPrinterSelector = {
    Component: SelectPrinterMenu,
};

registry
    .category("systray")
    .add("base_report_to_printer.printer_selector_button", systrayPrinterSelector, {
        sequence: 100,
    });
