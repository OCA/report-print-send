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
    label_format = fields.Selection(
        [("57x50", "57mm x 50mm"), ("50x18", "50mm x 18mm")], default="57x50"
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

    def format_printer_data(self):
        self.ensure_one()
        return {
            "url": self.url,
            "resolution": self.resolution,
            "format": self.label_format,
        }

    def get_default_printer(self):
        if self.env.user.zpl_printer_id:
            return self.env.user.zpl_printer_id
        printer = self.search([("default", "=", True)])
        if len(printer) >= 1:
            return printer[0]
        printer = self.search([])
        if len(printer) == 0:
            raise ValueError(_("No default printer specified"))
        return printer[0]

    def should_check_report_name(self):
        return self.env.user.printer_selection_strategy not in ["always_user_default"]

    def get_label_printer_data(
        self, report_name, active_ids, client_preferred_printer=False
    ):
        preferred_printer = self.handle_preferred_printer(client_preferred_printer)
        if preferred_printer:
            return preferred_printer
        default_printer = self.get_default_printer()
        return default_printer.format_printer_data()

    def handle_preferred_printer(self, client_preferred_printer=False):
        if not client_preferred_printer:
            return False
        preferred_printer = self.browse([client_preferred_printer])
        return (
            preferred_printer.format_printer_data()
            if len(preferred_printer) == 1
            else False
        )
