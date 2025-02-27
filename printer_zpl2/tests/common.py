from odoo.addons.base.tests.common import BaseCommon

model = "odoo.addons.base_report_to_printer.models.printing_server"


class PrinterZpl2Common(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Model = cls.env["printing.label.zpl2"]
        cls.ComponentModel = cls.env["printing.label.zpl2.component"]
        cls.server = cls.env["printing.server"].create({})
        cls.printer = cls.env["printing.printer"].create(
            {
                "name": "Printer",
                "server_id": cls.server.id,
                "system_name": "Sys Name",
                "default": True,
                "status": "unknown",
                "status_message": "Msg",
                "model": "res.users",
                "location": "Location",
                "uri": "URI",
            }
        )
        cls.label_vals = {
            "name": "ZPL II Label",
            "model_id": cls.env.ref("base_report_to_printer.model_printing_printer").id,
        }
        cls.label = cls.env["printing.label.zpl2"].create(cls.label_vals)
