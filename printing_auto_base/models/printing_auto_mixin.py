# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class PrintingAutoMixin(models.AbstractModel):
    _name = "printing.auto.mixin"
    _description = "Printing Auto Mixin"

    auto_printing_ids = fields.Many2many(
        "printing.auto", string="Auto Printing Configuration"
    )
    printing_auto_error = fields.Text("Printing error")

    def _on_printing_auto_start(self):
        self.write({"printing_auto_error": False})

    def _printing_auto_done_post(self, auto, printer, count):
        self.ensure_one()
        self.message_post(
            body=_("{name}: {count} document(s) sent to printer {printer}").format(
                name=auto.name, count=count, printer=printer.name
            )
        )

    def _on_printing_auto_done(self, auto, printer, count):
        self._printing_auto_done_post(auto, printer, count)

    def _on_printing_auto_error(self, e):
        self.write({"printing_auto_error": str(e)})

    def _get_printing_auto(self):
        return self.auto_printing_ids

    def _do_print_auto(self, printing_auto):
        self.ensure_one()
        printing_auto.ensure_one()
        printer, count = printing_auto.do_print(self)
        if count:
            self._on_printing_auto_done(printing_auto, printer, count)

    def _handle_print_auto(self, printing_auto):
        printing_auto.ensure_one()
        if printing_auto.action_on_error == "raise":
            self._do_print_auto(printing_auto)
            return
        try:
            with self.env.cr.savepoint():
                self._do_print_auto(printing_auto)
        except Exception as e:
            _logger.exception(
                "An error occurred while printing '%s' for record %s.",
                printing_auto,
                self,
            )
            self._on_printing_auto_error(e)

    def handle_print_auto(self):
        """Print some report or attachment directly to the corresponding printer."""
        self._on_printing_auto_start()
        for record in self:
            for printing_auto in record._get_printing_auto():
                record._handle_print_auto(printing_auto)
