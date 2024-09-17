# Copyright 2016 LasLabs Inc.
# Copyright 2016 SYLEAM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo.tests.common import TransactionCase

model = "odoo.addons.base.models.ir_actions_report.IrActionsReport"


class TestIrActionsReportXml(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Model = self.env["ir.actions.report"]
        self.vals = {}

        self.report = self.env["ir.actions.report"].search([], limit=1)
        self.server = self.env["printing.server"].create({})

    def new_action(self):
        return self.env["printing.action"].create(
            {"name": "Printing Action", "action_type": "server"}
        )

    def new_printing_action(self):
        return self.env["printing.report.xml.action"].create(
            {
                "report_id": self.report.id,
                "user_id": self.env.ref("base.user_demo").id,
                "action": "server",
            }
        )

    def new_printer(self):
        return self.env["printing.printer"].create(
            {
                "name": "Printer",
                "server_id": self.server.id,
                "system_name": "Sys Name",
                "default": True,
                "status": "unknown",
                "status_message": "Msg",
                "model": "res.users",
                "location": "Location",
                "uri": "URI",
            }
        )

    def new_tray(self, tray_type="input", vals=None, defaults=None):
        values = dict(defaults)
        if vals is not None:
            values.update(vals)
        return self.env["printing.tray." + tray_type].create(values)

    def test_print_action_for_report_name_gets_report(self):
        """It should get report by name"""
        with mock.patch("%s._get_report_from_name" % model) as mk:
            expect = "test"
            self.Model.print_action_for_report_name(expect)
            mk.assert_called_once_with(expect)

    def test_print_action_for_report_name_returns_if_no_report(self):
        """It should return empty dict when no matching report"""
        with mock.patch("%s._get_report_from_name" % model) as mk:
            expect = "test"
            mk.return_value = False
            res = self.Model.print_action_for_report_name(expect)
            self.assertDictEqual({}, res)

    def test_print_action_for_report_name_returns_if_report(self):
        """It should return correct serializable result for behaviour"""
        with mock.patch("%s._get_report_from_name" % model) as mk:
            res = self.Model.print_action_for_report_name("test")
            behaviour = mk().behaviour()
            expect = {
                "action": behaviour["action"],
                "printer_name": behaviour["printer"].name,
            }
            self.assertDictEqual(expect, res, f"Expect {expect}, Got {res}")

    def test_behaviour_default_values(self):
        """It should return the default action and printer"""
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = False
        self.env.user.printing_printer_id = False
        report.property_printing_action_id = False
        report.printing_printer_id = False
        self.assertEqual(
            report.behaviour(),
            {
                "action": "client",
                "printer": self.env["printing.printer"],
                "input_tray": False,
                "output_tray": False,
            },
        )

    def test_behaviour_user_values(self):
        """It should return the action and printer from user"""
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "client"
        self.env.user.printing_printer_id = self.new_printer()
        self.assertEqual(
            report.behaviour(),
            {
                "action": "client",
                "printer": self.env.user.printing_printer_id,
                "input_tray": False,
                "output_tray": False,
            },
        )

    def test_behaviour_report_values(self):
        """It should return the action and printer from report"""
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "client"
        report.property_printing_action_id = self.new_action()
        report.printing_printer_id = self.new_printer()
        self.assertEqual(
            report.behaviour(),
            {
                "action": report.property_printing_action_id.action_type,
                "printer": report.printing_printer_id,
                "input_tray": False,
                "output_tray": False,
            },
        )

    def test_behaviour_user_action(self):
        """It should return the action and printer from user action"""
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "client"
        report.property_printing_action_id.action_type = "user_default"
        self.assertEqual(
            report.behaviour(),
            {
                "action": "client",
                "printer": report.printing_printer_id,
                "input_tray": False,
                "output_tray": False,
            },
        )

    def test_behaviour_printing_action_on_wrong_user(self):
        """It should return the action and printer ignoring printing action"""
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "client"
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env["res.users"].search(
            [("id", "!=", self.env.user.id)], limit=1
        )
        self.assertEqual(
            report.behaviour(),
            {
                "action": "client",
                "printer": report.printing_printer_id,
                "input_tray": False,
                "output_tray": False,
            },
        )

    def test_behaviour_printing_action_on_wrong_report(self):
        """It should return the action and printer ignoring printing action"""
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "client"
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env.user
        printing_action.report_id = self.env["ir.actions.report"].search(
            [("id", "!=", report.id)], limit=1
        )
        self.assertEqual(
            report.behaviour(),
            {
                "action": "client",
                "printer": report.printing_printer_id,
                "input_tray": False,
                "output_tray": False,
            },
        )

    def test_behaviour_printing_action_with_no_printer(self):
        """It should return the action from printing action and printer from
        other
        """
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "client"
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env.user
        printing_action.report_id = report
        self.assertEqual(
            report.behaviour(),
            {
                "action": printing_action.action,
                "printer": report.printing_printer_id,
                "input_tray": False,
                "output_tray": False,
            },
        )

    def test_behaviour_printing_action_with_printer(self):
        """It should return the action and printer from printing action"""
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "client"
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env.user
        printing_action.printer_id = self.new_printer()
        self.assertEqual(
            report.behaviour(),
            {
                "action": printing_action.action,
                "printer": printing_action.printer_id,
                "input_tray": False,
                "output_tray": False,
            },
        )

    def test_behaviour_printing_action_user_defaults(self):
        """It should return the action and printer from user with printing
        action
        """
        report = self.Model.search([], limit=1)
        self.env.user.printing_action = "client"
        printing_action = self.new_printing_action()
        printing_action.user_id = self.env.user
        printing_action.action = "user_default"
        self.assertEqual(
            report.behaviour(),
            {
                "action": "client",
                "printer": report.printing_printer_id,
                "input_tray": False,
                "output_tray": False,
            },
        )

    def test_print_tray_behaviour(self):
        """
        It should return the correct tray
        """
        report = self.env["ir.actions.report"].search([], limit=1)
        action = self.env["printing.report.xml.action"].create(
            {"user_id": self.env.user.id, "report_id": report.id, "action": "server"}
        )
        printer = self.new_printer()
        tray_vals = {
            "name": "Tray",
            "system_name": "Tray",
            "printer_id": printer.id,
        }
        user_tray_in = self.new_tray("input", {"system_name": "User tray"}, tray_vals)
        report_tray_in = self.new_tray(
            "input", {"system_name": "Report tray"}, tray_vals
        )
        action_tray_in = self.new_tray(
            "input", {"system_name": "Action tray"}, tray_vals
        )
        user_tray_out = self.new_tray("output", {"system_name": "User tray"}, tray_vals)
        report_tray_out = self.new_tray(
            "output", {"system_name": "Report tray"}, tray_vals
        )
        action_tray_out = self.new_tray(
            "output", {"system_name": "Action tray"}, tray_vals
        )

        # No report passed
        self._set_trays(report, action, "input")
        self._set_trays(report, action, "output")
        options = printer.print_options()
        self.assertFalse("InputSlot" in options)
        self.assertFalse("OutputBin" in options)

        # No tray defined
        self._set_trays(report, action, "input")
        self._set_trays(report, action, "output")
        options = report.behaviour()
        self.assertTrue("input_tray" in options)
        self.assertTrue("output_tray" in options)

        # Only user tray is defined
        self._set_trays(report, action, "input", user_tray_in)
        self._set_trays(report, action, "output", user_tray_out)
        self.assertEqual("User tray", report.behaviour()["input_tray"])
        self.assertEqual("User tray", report.behaviour()["output_tray"])

        # Only report tray is defined
        self._set_trays(report, action, "input", report_tray=report_tray_in)
        self._set_trays(report, action, "output", report_tray=report_tray_out)
        self.assertEqual("Report tray", report.behaviour()["input_tray"])
        self.assertEqual("Report tray", report.behaviour()["output_tray"])

        # Only action tray is defined
        self._set_trays(report, action, "input", action_tray=action_tray_in)
        self._set_trays(report, action, "output", action_tray=action_tray_out)
        self.assertEqual("Action tray", report.behaviour()["input_tray"])
        self.assertEqual("Action tray", report.behaviour()["output_tray"])

        # User and report tray defined
        self._set_trays(report, action, "input", user_tray_in, report_tray_in)
        self._set_trays(report, action, "output", user_tray_out, report_tray_out)
        self.assertEqual("Report tray", report.behaviour()["input_tray"])
        self.assertEqual("Report tray", report.behaviour()["output_tray"])

        # All trays are defined
        self._set_trays(
            report, action, "input", user_tray_in, report_tray_in, action_tray_in
        )
        self._set_trays(
            report, action, "output", user_tray_out, report_tray_out, action_tray_out
        )
        self.assertEqual("Action tray", report.behaviour()["input_tray"])
        self.assertEqual("Action tray", report.behaviour()["output_tray"])

    def _set_trays(
        self,
        report,
        action,
        tray_type="input",
        user_tray=False,
        report_tray=False,
        action_tray=False,
    ):
        attr = "printer_" + tray_type + "_tray_id"
        setattr(self.env.user, attr, user_tray)
        setattr(report, attr, report_tray)
        setattr(action, attr, action_tray)

    def test_onchange_printer_tray_id_empty(self):
        action = self.env["ir.actions.report"].new(
            {
                "printer_input_tray_id": False,
                "printer_output_tray_id": False,
            }
        )
        action.onchange_printing_printer_id()
        self.assertFalse(action.printer_input_tray_id)
        self.assertFalse(action.printer_output_tray_id)

    def test_onchange_printer_tray_id_not_empty(self):
        server = self.env["printing.server"].create({})
        printer = self.env["printing.printer"].create(
            {
                "name": "Printer",
                "server_id": server.id,
                "system_name": "Sys Name",
                "default": True,
                "status": "unknown",
                "status_message": "Msg",
                "model": "res.users",
                "location": "Location",
                "uri": "URI",
            }
        )
        input_tray = self.env["printing.tray.input"].create(
            {
                "name": "Tray",
                "system_name": "TrayName",
                "printer_id": printer.id,
            }
        )
        output_tray = self.env["printing.tray.output"].create(
            {
                "name": "Tray",
                "system_name": "TrayName",
                "printer_id": printer.id,
            }
        )

        action = self.env["ir.actions.report"].new(
            {
                "printer_input_tray_id": input_tray.id,
                "printer_output_tray_id": output_tray.id,
            }
        )
        self.assertEqual(action.printer_input_tray_id, input_tray)
        self.assertEqual(action.printer_output_tray_id, output_tray)
        action.onchange_printing_printer_id()
        self.assertFalse(action.printer_input_tray_id)
        self.assertFalse(action.printer_output_tray_id)
