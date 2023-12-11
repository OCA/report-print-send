# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# Copyright (C) 2016 SYLEAM (<http://www.syleam.fr>)
# Copyright (C) 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os
from tempfile import mkstemp

from odoo import exceptions, fields, models

_logger = logging.getLogger(__name__)


class PrintingPrinter(models.Model):
    _name = "printing.printer"
    _description = "Logical Printer"

    name = fields.Char(required=True)
    system_name = fields.Char(required=True)
    backend = fields.Selection(
        selection=[("base", "Base")],
        required=True,
        default="base",
    )
    active = fields.Boolean(default=True)
    default = fields.Boolean(readonly=True)
    status = fields.Selection(
        selection=[
            ("unavailable", "Unavailable"),
            ("printing", "Printing"),
            ("unknown", "Unknown"),
            ("available", "Available"),
            ("error", "Error"),
            ("server-error", "Server Error"),
        ],
        required=True,
        readonly=True,
        default="unknown",
    )
    status_message = fields.Char(readonly=True)
    model = fields.Char(readonly=True)
    location = fields.Char(readonly=True)
    uri = fields.Char(string="URI", readonly=True)
    multi_thread = fields.Boolean()

    @staticmethod
    def _set_option_doc_format(report, value):
        return {"raw": "True"} if value == "raw" else {}

    _set_option_format = _set_option_doc_format

    @staticmethod
    def _set_option_noop(report, value):
        return {}

    def _set_option_input_tray(self, report, value):
        """Note we use self here as some older PPD use tray
        rather than InputSlot so we may need to query printer in override"""
        return {"InputSlot": str(value)} if value else {}

    def _set_option_output_tray(self, report, value):
        return {"OutputBin": str(value)} if value else {}

    _set_option_action = _set_option_noop
    _set_option_printer = _set_option_noop

    def print_options(self, report=None, **print_opts):
        options = {}
        for option, value in print_opts.items():
            try:
                options.update(getattr(self, f"_set_option_{option}")(report, value))
            except AttributeError:
                options[option] = str(value)
        return options

    def print_document(
        self, report, content, action=None, doc_format="qweb-pdf", **kwargs
    ):
        """Generic document print logic, backend-agnostic."""
        self.ensure_one()
        fd, file_name = mkstemp()
        if isinstance(content, str):
            content = content.encode("utf-8")
        try:
            os.write(fd, content)
        finally:
            os.close(fd)
        try:
            self.print_file(file_name, report=report, **kwargs)
        except Exception as e:
            raise exceptions.UserError(
                self.env._("Failed to print document: %(error)s", error=e)
            ) from e
        finally:
            try:
                os.remove(file_name)
            except OSError as err:
                _logger.warning(f"Unable to remove temporary file {file_name}: {err}")
        return True

    def print_file(self, file_name, report=None, **print_opts):
        _logger.debug(
            f"Generic print_file() called for {self.name}\
            with file '{file_name}' and options: {print_opts}."
        )
        return False

    def print_test_page(self):
        _logger.debug(f"Generic print_test_page() called for {self.name}.")
        return False

    def cancel_all_jobs(self, purge_jobs=False):
        _logger.debug(f"Generic cancel_all_jobs() called for {self.name}.")
        return False

    def enable(self):
        _logger.debug(f"Generic enable() called for {self.name}.")
        return False

    def disable(self):
        _logger.debug(f"Generic disable() called for {self.name}.")
        return False

    def set_default(self):
        if not self:
            return
        self.ensure_one()
        default_printers = self.search([("default", "=", True)])
        default_printers.unset_default()
        self.write({"default": True})
        return True

    def unset_default(self):
        self.write({"default": False})
        return True

    def get_default(self):
        return self.search([("default", "=", True)], limit=1)

    def action_cancel_all_jobs(self):
        self.ensure_one()
        return self.cancel_all_jobs()
