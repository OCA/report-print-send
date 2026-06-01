from odoo import models


class ZplPrinter(models.Model):
    _inherit = "zpl_printer.zpl_printer"

    def get_label_printer_data(
        self, report_name, active_ids, client_preferred_printer=False
    ):
        """
        During production, the workcenter might specify a different labelprinter,
        as this would be, where the item is at that time, that printer should be used.

        :param report_name: string
        :param active_ids: int[]
        :return: {"url": string, "resolution": string}
        """

        preferred_printer = self.handle_preferred_printer(client_preferred_printer)
        if preferred_printer:
            return preferred_printer

        if self.should_check_report_name() and report_name in [
            "mrp.label_production_view",
            "stock.label_lot_template_view",
        ]:
            if report_name == "mrp.label_production_view":
                productions = self.env["mrp.production"].browse(active_ids)
            elif report_name == "stock.label_lot_template_view":
                productions = self.env["mrp.production"].search(
                    [
                        ("lot_producing_id", "in", active_ids),
                        ("state", "in", ["confirmed", "progress", "to_close"]),
                    ]
                )
            for production in productions:
                for workorder in production.workorder_ids.filtered(
                    lambda wo: wo.state in ["ready", "progress", "done"]
                ):
                    if workorder.workcenter_id.zpl_printer_id:
                        return (
                            workorder.workcenter_id.zpl_printer_id.format_printer_data()
                        )
                if production.product_id.product_tmpl_id.zpl_printer_id:
                    return production.product_id.product_tmpl_id.zpl_printer_id.format_printer_data()
        return super().get_label_printer_data(report_name, active_ids)
