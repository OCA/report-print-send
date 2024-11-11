# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
# Copyright (C) 2013-2014 Camptocamp (<http://www.camptocamp.com>)
# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import threading
from time import time

from odoo import _, api, exceptions, fields, models, registry
from odoo.tools.safe_eval import safe_eval

REPORT_TYPES = {"qweb-pdf": "pdf", "qweb-text": "text"}


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    property_printing_action_id = fields.Many2one(
        comodel_name="printing.action",
        string="Default Behaviour",
        company_dependent=True,
    )
    printing_printer_id = fields.Many2one(
        comodel_name="printing.printer", string="Default Printer"
    )
    printer_tray_id = fields.Many2one(
        comodel_name="printing.tray",
        string="Paper Source",
        domain="[('printer_id', '=', printing_printer_id)]",
    )
    printing_action_ids = fields.One2many(
        comodel_name="printing.report.xml.action",
        inverse_name="report_id",
        string="Actions",
        help="This field allows configuring action and printer on a per " "user basis",
    )

    @api.onchange("printing_printer_id")
    def onchange_printing_printer_id(self):
        """Reset the tray when the printer is changed"""
        self.printer_tray_id = False

    @api.model
    def print_action_for_report_name(self, report_name):
        """Returns if the action is a direct print or pdf

        Called from js
        """
        report = self._get_report_from_name(report_name)
        if not report:
            return {}
        result = report.behaviour()
        serializable_result = {
            "action": result["action"],
            "printer_name": result["printer"].name,
        }
        if result.get("printer_exception") and not self.env.context.get(
            "skip_printer_exception"
        ):
            serializable_result["printer_exception"] = True
        if self.env.context.get("force_print_to_client"):
            serializable_result["action"] = "client"
        return serializable_result

    def _get_user_default_print_behaviour(self):
        printer_obj = self.env["printing.printer"]
        user = self.env.user
        return dict(
            action=user.printing_action or "client",
            printer=user.printing_printer_id or printer_obj.get_default(),
            tray=(
                str(user.printer_tray_id.system_name) if user.printer_tray_id else False
            ),
        )

    def _get_report_default_print_behaviour(self):
        result = {}
        report_action = self.property_printing_action_id
        if report_action and report_action.action_type != "user_default":
            result["action"] = report_action.action_type
        if self.printing_printer_id:
            result["printer"] = self.printing_printer_id
        if self.printer_tray_id:
            result["tray"] = self.printer_tray_id.system_name
        return result

    def behaviour(self):
        self.ensure_one()
        printing_act_obj = self.env["printing.report.xml.action"]

        result = self._get_user_default_print_behaviour()
        result.update(self._get_report_default_print_behaviour())

        # Retrieve report-user specific values
        print_action = printing_act_obj.search(
            [
                ("report_id", "=", self.id),
                ("user_id", "=", self.env.uid),
                ("action", "!=", "user_default"),
            ],
            limit=1,
        )
        if print_action:
            # For some reason design takes report defaults over
            # False action entries so we must allow for that here
            result.update({k: v for k, v in print_action.behaviour().items() if v})
        printer = result.get("printer")
        if printer:
            # When no printer is available we can fallback to the default behavior
            # letting the user to manually print the reports.
            try:
                printer.server_id._open_connection(raise_on_error=True)
                printer_exception = printer.status in [
                    "error",
                    "server-error",
                    "unavailable",
                ]
            except Exception:
                printer_exception = True
            if printer_exception and not self.env.context.get("skip_printer_exception"):
                result["printer_exception"] = True
        return result

    def print_document_client_action(self, record_ids, data=None):
        behaviour = self.behaviour()
        printer = behaviour.pop("printer", None)
        if printer.multi_thread:

            @self.env.cr.postcommit.add
            def _launch_print_thread():
                threaded_calculation = threading.Thread(
                    target=self.print_document_threaded,
                    args=(self.id, record_ids, data),
                )
                threaded_calculation.start()

            return True
        else:
            try:
                return self.print_document(record_ids, data=data)
            except Exception:
                return

    def print_document_threaded(self, report_id, record_ids, data):
        with registry(self._cr.dbname).cursor() as cr:
            self = self.with_env(self.env(cr=cr))
            report = self.env["ir.actions.report"].browse(report_id)
            report.print_document(record_ids, data)

    def print_document(self, record_ids, data=None):
        """Print a document, do not return the document file"""
        report_type = REPORT_TYPES.get(self.report_type)
        if not report_type:
            raise exceptions.UserError(
                _("This report type (%s) is not supported by direct printing!")
                % str(self.report_type)
            )
        method_name = "_render_qweb_%s" % (report_type)
        document, doc_format = getattr(
            self.with_context(must_skip_send_to_printer=True), method_name
        )(self.report_name, record_ids, data=data)
        behaviour = self.behaviour()
        printer = behaviour.pop("printer", None)

        if not printer:
            raise exceptions.UserError(_("No printer configured to print this report."))
        if self.print_report_name:
            report_file_names = [
                safe_eval(self.print_report_name, {"object": obj, "time": time})
                for obj in self.env[self.model].browse(record_ids)
            ]
            title = " ".join(report_file_names)
            if len(title) > 80:
                title = title[:80] + "…"
        else:
            title = self.report_name
        behaviour["title"] = title
        behaviour["res_ids"] = record_ids
        # TODO should we use doc_format instead of report_type
        return printer.print_document(
            self, document, doc_format=self.report_type, **behaviour
        )

    def _can_print_report(self, behaviour, printer, document):
        """Predicate that decide if report can be sent to printer

        If you want to prevent `render_qweb_pdf` to send report you can set
        the `must_skip_send_to_printer` key to True in the context
        """
        if self.env.context.get("must_skip_send_to_printer"):
            return False
        if (
            behaviour["action"] == "server"
            and printer
            and document
            and not behaviour.get("printer_exception")
        ):
            return True
        return False

    def report_action(self, docids, data=None, config=True):
        res = super().report_action(docids, data=data, config=config)
        if not res.get("id"):
            res["id"] = self.id
        return res

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """Generate a PDF and returns it.

        If the action configured on the report is server, it prints the
        generated document as well.
        """
        document, doc_format = super()._render_qweb_pdf(
            report_ref, res_ids=res_ids, data=data
        )
        report = self._get_report(report_ref)
        behaviour = report.behaviour()
        printer = behaviour.pop("printer", None)
        can_print_report = report._can_print_report(behaviour, printer, document)

        if can_print_report:
            printer.print_document(
                report, document, doc_format=report.report_type, **behaviour
            )

        return document, doc_format

    def _render_qweb_text(self, report_ref, docids, data=None):
        """Generate a TEXT file and returns it.

        If the action configured on the report is server, it prints the
        generated document as well.
        """
        document, doc_format = super()._render_qweb_text(
            report_ref, docids=docids, data=data
        )
        report = self._get_report(report_ref)
        behaviour = report.behaviour()
        printer = behaviour.pop("printer", None)
        can_print_report = report._can_print_report(behaviour, printer, document)

        if can_print_report:
            printer.print_document(
                report, document, doc_format=report.report_type, **behaviour
            )

        return document, doc_format
