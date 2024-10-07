from odoo import models


class ZplPrinter(models.Model):
    _inherit = "zpl_printer.zpl_printer"

    def get_label_printer_data(self, report_name, active_ids):
        if report_name == "stock.label_lot_template_view":
            for lot in self.env["stock.lot"].browse(active_ids):
                if lot.product_id.product_tmpl_id.zpl_printer_id:
                    printer = lot.product_id.product_tmpl_id.zpl_printer_id
                    return {"url": printer.url, "resolution": printer.resolution}
        return super().get_label_printer_data(report_name, active_ids)
