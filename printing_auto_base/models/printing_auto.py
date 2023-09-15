# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


class PrintingAuto(models.Model):
    """Configure which document to print automatically. This model must be
    linked with a many2many relation from the another model from which you want
    to print a document"""

    _name = "printing.auto"
    _description = "Printing Auto"

    name = fields.Char(string="Name", required=True)

    data_source = fields.Selection(
        [
            ("report", "Report"),
            ("attachment", "Attachment"),
        ],
        string="Data source",
        default="report",
        required=True,
        help=(
            "Choose to print the result of an odoo report or a pre-existing "
            "attachment (useful for labels received from carriers that are "
            "recorded on the picking as an attachment)"
        ),
    )
    report_id = fields.Many2one("ir.actions.report")
    attachment_domain = fields.Char("Attachment domain", default="[]")

    condition = fields.Char(
        "Condition",
        default="[]",
        help="Give a domain that must be valid for printing this",
    )
    record_change = fields.Char(
        "Record change",
        help="Select on which document the report must be executed. Use a path "
        "using a dotted notation starting from any record field. For "
        "example, if your record is a stock.picking, you can access the "
        "next picking with 'move_lines.move_dest_ids.picking_id'",
    )

    printer_id = fields.Many2one("printing.printer", "Printer")
    printer_tray_id = fields.Many2one("printing.tray", "Tray")
    nbr_of_copies = fields.Integer("Number of Copies", default=1)
    action_on_error = fields.Selection(
        [("log", "Record an error"), ("raise", "Raise an Exception")],
        "Action on error",
        default="log",
        required=True,
    )

    @api.constrains("data_source", "report_id", "attachment_domain")
    def _check_data_source(self):
        for rec in self:
            if rec.data_source == "report" and not rec.report_id:
                raise UserError(_("Report is not set"))
            if rec.data_source == "attachment" and (
                not rec.attachment_domain or rec.attachment_domain == "[]"
            ):
                raise UserError(_("Attachment domain is not set"))

    def _get_behaviour(self):
        if self.printer_id:
            result = {"printer": self.printer_id}
            if self.printer_tray_id:
                result["tray"] = self.printer_tray_id.system_name
            return result
        if self.data_source == "report":
            return self.report_id.behaviour()
        return self.env["ir.actions.report"]._get_user_default_print_behaviour()

    def _get_record(self, record):
        if self.record_change:
            try:
                return safe_eval(f"obj.{self.record_change}", {"obj": record})
            except Exception as e:
                raise ValidationError(
                    _("The Record change could not be applied because: %s") % str(e)
                ) from e
        return record

    def _check_condition(self, record):
        domain = safe_eval(self.condition, {"env": self.env})
        return record.filtered_domain(domain)

    def _get_content(self, records):
        generate_data_func = getattr(
            self, f"_generate_data_from_{self.data_source}", None
        )
        content = []
        if generate_data_func:
            records = self._get_record(records)
            for record in records:
                content.append(generate_data_func(record)[0])
        return content

    def _prepare_attachment_domain(self, record):
        domain = safe_eval(self.attachment_domain)
        record_domain = [
            ("res_id", "=", record.id),
            ("res_model", "=", record._name),
        ]
        return expression.AND([domain, record_domain])

    def _generate_data_from_attachment(self, record):
        domain = self._prepare_attachment_domain(record)
        attachments = self.env["ir.attachment"].search(domain)
        if not attachments:
            raise ValidationError(_("No attachment was found."))
        return [base64.b64decode(a.datas) for a in attachments]

    def _generate_data_from_report(self, record):
        self.ensure_one()
        data, _ = self.report_id.with_context(must_skip_send_to_printer=True)._render(
            record.id
        )
        return [data]

    def do_print(self, records):
        self.ensure_one()

        behaviour = self._get_behaviour()
        printer = behaviour["printer"]

        if self.nbr_of_copies <= 0:
            return (printer, 0)
        records = self._check_condition(records)
        if not records:
            return (printer, 0)

        if not printer:
            raise UserError(
                _("No printer configured to print this {}.").format(self.name)
            )

        count = 0
        for content in self._get_content(records):
            for _n in range(self.nbr_of_copies):
                printer.print_document(report=None, content=content, **behaviour)
                count += 1
        return (printer, count)
