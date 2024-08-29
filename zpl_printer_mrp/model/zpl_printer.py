from odoo import models


class ZplPrinter(models.Model):
    _inherit = "zpl_printer.zpl_printer"

    def get_label_printer_data(self, report_name, active_ids):
        if report_name == "mrp.label_production_view":
            for production in self.env["mrp.production"].browse(active_ids):
                if production.product_id.product_tmpl_id.zpl_printer_id:
                    printer = production.product_id.product_tmpl_id.zpl_printer_id
                    return {"url": printer.url, "resolution": printer.resolution}
        return super().get_label_printer_data(report_name, active_ids)
