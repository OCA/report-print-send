# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.printing_auto_base.tests.common import TestPrintingAutoCommon


class TestPrintingAutoBase(TestPrintingAutoCommon):
    def test_behaviour_label(self):
        self.env.user.default_label_printer_id = self.printer_2
        expected = {"printer": self.printer_2}
        printing_auto = self._create_printing_auto_attachment({"is_label": True})
        self.assertEqual(expected, printing_auto._get_behaviour())
