# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import fields, models

from ..escpos import Printer


class PrintingEscpos(models.Model):
    _name = "printing.escpos"
    _description = "Print Escpos"

    name = fields.Char(required=True)
    model_id = fields.Many2one("ir.model", required=True)
    mode = fields.Selection(
        [("report", "Report"), ("arch", "Manual")], required=True, default="report"
    )
    model = fields.Char(
        related="model_id.model", readonly=True, string="Model reference"
    )
    report_id = fields.Many2one("ir.actions.report")
    active = fields.Boolean(default=True)
    test_print_mode = fields.Boolean(string="Mode Print")
    record_id = fields.Integer(string="Record ID", default=1)
    printer_id = fields.Many2one(comodel_name="printing.printer", string="Printer")
    arch = fields.Text()

    def _render(self, record):
        if self.mode == "report":
            return self.report_id.render_qweb_text(record.ids)[0]
        qcontext = self.env["ir.ui.view"]._prepare_qcontext()
        qcontext.update(
            {"doc_ids": record.ids, "doc_model": self.model, "docs": record}
        )
        return self.env["ir.qweb"].render(etree.fromstring(self.arch), qcontext)

    def print_test_escpos(self):
        self.print_escpos(self.printer_id, self.env[self.model].browse(self.record_id))

    def print_escpos(self, printer, record):
        data = self._render(record)
        escpos_printer = Printer()
        escpos_printer.print_xml(data)
        printer.print_document(
            report=None, content=escpos_printer.output, doc_format="raw"
        )
