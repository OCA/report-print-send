# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.exceptions import UserError, ValidationError

from .common import PrintingPrinter, TestPrintingAutoCommon, print_document


@mock.patch.object(PrintingPrinter, "print_document", print_document)
class TestPrintingAutoBase(TestPrintingAutoCommon):
    def test_check_data_source(self):
        with self.assertRaises(UserError):
            self._create_printing_auto_report({"report_id": False})

        with self.assertRaises(UserError):
            self._create_printing_auto_attachment({"attachment_domain": "[]"})

        with self.assertRaises(UserError):
            printing_auto = self._create_printing_auto_attachment()
            printing_auto.attachment_domain = False

    def test_behaviour(self):
        expected = {"printer": self.printer_1}
        printing_auto = self._create_printing_auto_report(
            {"printer_id": self.printer_1.id}
        )
        self.assertEqual(expected, printing_auto._get_behaviour())

        printing_auto.printer_tray_id = self.tray_1
        expected["tray"] = self.tray_1.system_name
        self.assertEqual(expected, printing_auto._get_behaviour())

        expected = printing_auto.report_id.behaviour()
        printing_auto.printer_id = False
        printing_auto.printer_tray_id = False
        self.assertEqual(expected, printing_auto._get_behaviour())

        expected = self.env["ir.actions.report"]._get_user_default_print_behaviour()
        printing_auto = self._create_printing_auto_attachment()
        self.assertEqual(expected, printing_auto._get_behaviour())

    def test_record_change(self):
        parent = self.env["res.partner"].create({"name": "Parent"})
        partner = parent.create({"name": "Child", "parent_id": parent.id})
        printing_auto = self._create_printing_auto_report(
            {"record_change": "parent_id"}
        )
        self.assertEqual(parent, printing_auto._get_record(partner))

    def test_check_condition(self):
        partner = self.env["res.partner"].create({"name": "Partner"})
        printing_auto = self._create_printing_auto_report(
            {"condition": f"[('name', '=', '{partner.name}')]"}
        )
        self.assertEqual(partner, printing_auto._check_condition(partner))
        printing_auto.condition = "[('name', '=', '1')]"
        self.assertFalse(printing_auto._check_condition(partner))

    def test_get_content(self):
        printing_auto_report = self._create_printing_auto_report()
        self.assertEqual([self.data], printing_auto_report._get_content(self.record))

        printing_auto_attachment = self._create_printing_auto_attachment()
        attachment = self._create_attachment(self.record, self.data, "1")
        self.assertEqual(
            [attachment.raw], printing_auto_attachment._get_content(self.record)
        )
        attachment.unlink()

        with self.assertRaises(ValidationError):
            printing_auto_attachment._get_content(self.record)

    def test_do_print(self):
        printing_auto = self._create_printing_auto_attachment(
            {"attachment_domain": "[('name', 'like', 'printing_auto_test')]"}
        )
        self._create_attachment(self.record, self.data, "1")
        with self.assertRaises(UserError):
            printing_auto.do_print(self.record)

        printing_auto.printer_id = self.printer_1
        for nbr_of_copies in [0, 2, 1]:
            expected = (self.printer_1, nbr_of_copies)
            printing_auto.nbr_of_copies = nbr_of_copies
            self.assertEqual(expected, printing_auto.do_print(self.record))

        printing_auto.condition = "[('name', '=', 'test_printing_auto')]"
        expected = (self.printer_1, 0)
        self.assertEqual(expected, printing_auto.do_print(self.record))
