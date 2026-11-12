# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.tests import HttpCase, tagged

SERVER_MODEL = "odoo.addons.base_report_to_printer.models.printing_server"


@tagged("post_install", "-at_install")
class TestSelectPrinterUI(HttpCase):
    def test_printer_dialog(self):
        server = self.env["printing.server"].create({})
        printers = self.env["printing.printer"]
        printers.search([]).write({"active": False})
        for name in ("Alpha", "Beta"):
            printers |= printers.create(
                {
                    "name": name,
                    "system_name": name,
                    "server_id": server.id,
                    "status": "available",
                }
            )
        action = self.env["printing.action"].create(
            {"name": "Ask", "action_type": "select"}
        )
        report = self.env.ref("base.report_ir_model_overview")
        report.write(
            {
                "property_printing_action_id": action.id,
                "printing_printer_id": printers[1].id,
            }
        )
        code = f"""
            odoo.__WOWL_DEBUG__.root.env.services.action.doAction(
                {report.id}, {{additionalContext: {{active_ids: [1]}}}}
            );
            const check = () => {{
                const buttons = document.querySelectorAll(".o_printer_select .btn-lg");
                if (buttons.length === 2) {{
                    const selected = document.querySelector(
                        ".o_printer_select .o_printer_selected"
                    );
                    if (selected && selected.textContent.includes("Beta")) {{
                        console.log("test successful");
                        return;
                    }}
                    console.error("Wrong preselected printer");
                    return;
                }}
                setTimeout(check, 200);
            }};
            check();
        """
        with mock.patch(f"{SERVER_MODEL}.cups"):
            self.browser_js("/odoo", code, "odoo.isReady", login="admin")
