# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# Copyright (C) 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import errno
import logging
import os
from tempfile import mkstemp

from odoo import api, exceptions, fields, models

_logger = logging.getLogger(__name__)

try:
    import cups
except ImportError:
    _logger.debug("Cannot `import cups`.")


class PrintingPrinter(models.Model):
    _inherit = "printing.printer"

    server_id = fields.Many2one(comodel_name="printing.server", string="Server")
    job_ids = fields.One2many(
        comodel_name="printing.job",
        inverse_name="printer_id",
        string="Jobs",
    )
    tray_ids = fields.One2many(
        comodel_name="printing.tray", inverse_name="printer_id", string="Paper Sources"
    )
    multi_thread = fields.Boolean(
        compute="_compute_multi_thread", readonly=False, store=True
    )

    backend = fields.Selection(
        selection_add=[("cups", "CUPS")],
        ondelete={"cups": "cascade"},
    )

    @api.depends("server_id.multi_thread")
    def _compute_multi_thread(self):
        for printer in self:
            printer.multi_thread = printer.server_id.multi_thread

    def _prepare_update_from_cups(self, cups_connection, cups_printer):
        mapping = {3: "available", 4: "printing", 5: "error"}
        cups_vals = {
            "name": self.name or cups_printer["printer-info"],
            "backend": "cups",
            "model": cups_printer.get("printer-make-and-model", False),
            "location": cups_printer.get("printer-location", False),
            "uri": cups_printer.get("device-uri", False),
            "status": mapping.get(cups_printer.get("printer-state"), "unknown"),
            "status_message": cups_printer.get("printer-state-message", ""),
        }
        vals = {
            fieldname: value
            for fieldname, value in cups_vals.items()
            if not self or value != self[fieldname]
        }
        printer_uri = cups_printer["printer-uri-supported"]
        printer_system_name = printer_uri[printer_uri.rfind("/") + 1 :]
        try:
            ppd_info = cups_connection.getPPD3(printer_system_name)
        except Exception as e:
            raise exceptions.UserError(
                self.env._(
                    "Failed to get PPD for printer %(printer)s: %(error)s",
                    printer=printer_system_name,
                    error=str(e),
                )
            ) from e
        ppd_path = ppd_info[2]
        if not ppd_path:
            return vals
        ppd = cups.PPD(ppd_path)
        option = ppd.findOption("InputSlot")
        try:
            os.unlink(ppd_path)
        except OSError as err:
            if err.errno != errno.ENOENT:
                raise
        if not option:
            return vals
        tray_commands = []
        cups_trays = {
            tray_option["choice"]: tray_option["text"] for tray_option in option.choices
        }
        tray_commands.extend(
            [
                (0, 0, {"name": text, "system_name": choice})
                for choice, text in cups_trays.items()
                if choice not in self.tray_ids.mapped("system_name")
            ]
        )
        tray_commands.extend(
            [
                (2, tray.id)
                for tray in self.tray_ids.filtered(
                    lambda record: record.system_name not in cups_trays.keys()
                )
            ]
        )
        if tray_commands:
            vals["tray_ids"] = tray_commands
        return vals

    def print_file(self, file_name, report=None, **print_opts):
        super().print_file(file_name, report=report, **print_opts)
        self.ensure_one()
        title = print_opts.pop("title", file_name)
        connection = self.server_id._open_connection(raise_on_error=True)
        options = self.print_options(report=report, **print_opts)
        _logger.debug(
            f"Sending job to CUPS printer {self.system_name} on "
            f"{self.server_id.address} with options {options}"
        )
        try:
            connection.printFile(self.system_name, file_name, title, options=options)
        except Exception as e:
            raise exceptions.UserError(
                self.env._(
                    "Failed to print on printer %(printer)s: %(error)s",
                    printer=self.system_name,
                    error=str(e),
                )
            ) from e
        _logger.info(f"Printing job: '{file_name}' on {self.server_id.address}")
        try:
            os.remove(file_name)
        except OSError as exc:
            _logger.warning(f"Unable to remove temporary file {file_name}: {exc}")
        return True

    def cancel_all_jobs(self, purge_jobs=False):
        for printer in self:
            connection = printer.server_id._open_connection()
            try:
                connection.cancelAllJobs(
                    name=printer.system_name, purge_jobs=purge_jobs
                )
            except Exception as e:
                raise exceptions.UserError(
                    self.env._(
                        "Failed to cancel jobs on printer %(printer)s: %(error)s",
                        printer=printer.system_name,
                        error=str(e),
                    )
                ) from e
        self.mapped("server_id").update_jobs(which="completed")
        return True

    def enable(self):
        for printer in self:
            connection = printer.server_id._open_connection()
            try:
                connection.enablePrinter(printer.system_name)
            except Exception as e:
                raise exceptions.UserError(
                    self.env._(
                        "Failed to enable printer %(printer)s: %(error)s",
                        printer=printer.system_name,
                        error=str(e),
                    )
                ) from e
        self.mapped("server_id").update_printers()
        return True

    def disable(self):
        for printer in self:
            connection = printer.server_id._open_connection()
            try:
                connection.disablePrinter(printer.system_name)
            except Exception as e:
                raise exceptions.UserError(
                    self.env._(
                        "Failed to disable printer %(printer)s: %(error)s",
                        printer=printer.system_name,
                        error=str(e),
                    )
                ) from e
        self.mapped("server_id").update_printers()
        return True

    def print_test_page(self):
        for printer in self:
            connection = printer.server_id._open_connection()
            try:
                if printer.model == "Local Raw Printer":
                    fd, file_name = mkstemp()
                    try:
                        os.write(fd, b"TEST")
                    finally:
                        os.close(fd)
                    connection.printTestPage(printer.system_name, file=file_name)
                else:
                    connection.printTestPage(printer.system_name)
            except Exception as e:
                raise exceptions.UserError(
                    self.env._(
                        "Failed to print test page on printer %(printer)s: %(error)s",
                        printer=printer.system_name,
                        error=str(e),
                    )
                ) from e
        self.mapped("server_id").update_jobs(which="completed")
        return True
