import {Many2OneField, many2OneField} from "@web/views/fields/many2one/many2one_field";
import {registry} from "@web/core/registry";

export class ZPLLocalStoreMany2OneField extends Many2OneField {
    updateRecord(value) {
        localStorage.setItem("OdooPreferredZPLPrinter", JSON.stringify(value));
        return this.props.record.update({});
    }

    get value() {
        const preferred_printer = localStorage.getItem("OdooPreferredZPLPrinter");
        return preferred_printer ? JSON.parse(preferred_printer) : null;
    }
}

export const zplLocalStoreMany2OneField = {
    ...many2OneField,
    component: ZPLLocalStoreMany2OneField,
};

registry.category("fields").add("zpl_local_store_many2one", zplLocalStoreMany2OneField);
