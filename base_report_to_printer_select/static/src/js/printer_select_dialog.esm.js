/** @odoo-module **/
import {Component, onMounted, useRef, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";

const UNAVAILABLE_STATUSES = ["error", "server-error", "unavailable"];

export class PrinterSelectDialog extends Component {
    setup() {
        this.rootRef = useRef("root");
        this.state = useState({showAll: false});
        onMounted(() => {
            const selected = this.rootRef.el.querySelector(".o_printer_selected");
            const first = selected || this.rootRef.el.querySelector("button");
            if (first) {
                first.focus();
            }
        });
    }

    isUnavailable(printer) {
        return UNAVAILABLE_STATUSES.includes(printer.status);
    }

    buttonClass(printer) {
        if (printer.id === this.props.selectedId) {
            return "btn-primary o_printer_selected";
        }
        return this.isUnavailable(printer)
            ? "btn-outline-secondary"
            : "btn-outline-primary";
    }

    showAll() {
        this.state.showAll = true;
    }

    select(printer) {
        this.props.onSelect(printer.id);
        this.props.close();
    }

    download() {
        this.props.onSelect(null);
        this.props.close();
    }
}

PrinterSelectDialog.template = "base_report_to_printer_select.PrinterSelectDialog";
PrinterSelectDialog.components = {Dialog};
PrinterSelectDialog.props = {
    close: Function,
    title: String,
    printers: Array,
    otherPrinters: {type: Array, optional: true},
    selectedId: {type: [Number, Boolean], optional: true},
    onSelect: Function,
};
PrinterSelectDialog.defaultProps = {
    otherPrinters: [],
    selectedId: false,
};
