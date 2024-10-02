from odoo import _, fields, models


class ZplPrinter(models.Model):
    _name = "zpl_printer.zpl_printer"
    _description = "Label Printer"
    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            "The name must be unique.",
        ),
        (
            "url_unique",
            "unique(url)",
            "The url must be unique.",
        ),
    ]

    name = fields.Char()
    url = fields.Char()
    resolution = fields.Selection(
        [("200", "200"), ("300", "300")], "Printing Resolution (DPI)"
    )
    default = fields.Boolean()

    def write(self, vals):
        """There may only be one default."""
        if vals.get("default", False):
            for previous_default in self.search(
                [("default", "=", True), ("id", "!=", self.id)]
            ):
                previous_default.default = False
        return super().write(vals)

    def get_default_printer(self):
        printer = self.search([("default", "=", True)])
        if len(printer) >= 1:
            return printer[0]
        printer = self.search([])
        if len(printer) == 0:
            raise ValueError(_("No default printer specified"))
        return printer[0]

    def get_label_printer_data(self, report_name, active_ids):
        """This function is called from the client to determine which printer will be used.
        So this implementation just provides the default printer, but other modules will allow
        reacting more specific to this, for example to print a label for a certain product
        always on a different printer."""
        default_printer = self.get_default_printer()
        return {"url": default_printer.url, "resolution": default_printer.resolution}
