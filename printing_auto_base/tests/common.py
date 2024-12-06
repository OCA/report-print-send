# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests import common


def print_document(cls, *args, **kwargs):
    return


class TestPrintingAutoCommon(common.SavepointCase):
    @classmethod
    def _create_printer(cls, name):
        return cls.env["printing.printer"].create(
            {
                "name": name,
                "system_name": name,
                "server_id": cls.server.id,
            }
        )

    @classmethod
    def _create_tray(cls, name, printer):
        return cls.env["printing.tray"].create(
            {"name": name, "system_name": name, "printer_id": printer.id}
        )

    @classmethod
    def setUpReportAndRecord(cls):
        cls.report = cls.env.ref("base.report_ir_model_overview")
        cls.record = cls.env.ref("base.model_res_partner")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.server = cls.env["printing.server"].create({})
        for i in range(1, 4):
            printer_name = f"printer_{i}"
            tray_name = f"tray_{i}"
            printer = cls._create_printer(printer_name)
            tray = cls._create_tray(tray_name, printer)
            setattr(cls, printer_name, printer)
            setattr(cls, tray_name, tray)

        cls.setUpReportAndRecord()
        cls.data = cls.report._render(cls.record.id)[0]

    @classmethod
    def _create_printing_auto(cls, vals):
        vals.setdefault("model", "printing.auto")
        return cls.env["printing.auto"].create(vals)

    @classmethod
    def _create_attachment(cls, record, data, name_suffix):
        return cls.env["ir.attachment"].create(
            {
                "res_model": record._name,
                "res_id": record.id,
                "name": f"printing_auto_test_attachment_{name_suffix}.txt",
                "raw": data,
            }
        )

    @classmethod
    def _prepare_printing_auto_report_vals(cls):
        return {
            "data_source": "report",
            "report_id": cls.report.id,
            "name": "Printing auto report",
        }

    @classmethod
    def _create_printing_auto_report(cls, vals=None):
        _vals = cls._prepare_printing_auto_report_vals()
        _vals.update(vals or {})
        return cls._create_printing_auto(_vals)

    @classmethod
    def _prepare_printing_auto_attachment_vals(cls):
        return {
            "data_source": "attachment",
            "attachment_domain": "[('name', 'like', 'printing_auto_test_attachment')]",
            "name": "Printing auto attachment",
        }

    @classmethod
    def _create_printing_auto_attachment(cls, vals=None):
        _vals = cls._prepare_printing_auto_attachment_vals()
        _vals.update(vals or {})
        return cls._create_printing_auto(_vals)
