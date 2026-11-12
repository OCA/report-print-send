# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.tests import HttpCase, tagged

SERVER_MODEL = "odoo.addons.base_report_to_printer.models.printing_server"


@tagged("post_install", "-at_install")
class TestPrintingGroupUI(HttpCase):
    def test_see_more_shows_printers_outside_the_group(self):
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
        self.env["printing.group"].create(
            {
                "name": "Warehouse",
                "user_ids": [(6, 0, self.env.ref("base.user_admin").ids)],
                "printer_ids": [(6, 0, printers[0].ids)],
            }
        )
        action = self.env["printing.action"].create(
            {"name": "Ask", "action_type": "select"}
        )
        report = self.env.ref("base.report_ir_model_overview")
        report.property_printing_action_id = action
        code = f"""
            odoo.__WOWL_DEBUG__.root.env.services.action.doAction(
                {report.id}, {{additionalContext: {{active_ids: [1]}}}}
            );
            const checkAll = () => {{
                const buttons = document.querySelectorAll(".o_printer_select .btn-lg");
                if (buttons.length === 2) {{
                    console.log("test successful");
                    return;
                }}
                setTimeout(checkAll, 200);
            }};
            const check = () => {{
                const buttons = document.querySelectorAll(".o_printer_select .btn-lg");
                const more = document.querySelector(".o_printer_see_more");
                if (buttons.length === 1 && more) {{
                    if (!buttons[0].textContent.includes("Alpha")) {{
                        console.error("Wrong candidate printer");
                        return;
                    }}
                    more.click();
                    checkAll();
                    return;
                }}
                setTimeout(check, 200);
            }};
            check();
        """
        with mock.patch(f"{SERVER_MODEL}.cups"):
            self.browser_js("/odoo", code, "odoo.isReady", login="admin")
