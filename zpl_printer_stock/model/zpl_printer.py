from odoo import models


class ZplPrinter(models.Model):
    _inherit = "zpl_printer.zpl_printer"

    def get_label_printer_data(
        self, report_name, active_ids, client_preferred_printer=False
    ):
        preferred_printer = self.handle_preferred_printer(client_preferred_printer)
        if preferred_printer:
            return preferred_printer
        if (
            self.should_check_report_name()
            and report_name == "stock.label_lot_template_view"
        ):
            for lot in self.env["stock.lot"].browse(active_ids):
                if lot.product_id.product_tmpl_id.zpl_printer_id:
                    printer = lot.product_id.product_tmpl_id.zpl_printer_id
                    return printer.format_printer_data()
        return super().get_label_printer_data(report_name, active_ids)
