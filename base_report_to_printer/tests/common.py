# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import ClassVar

from odoo.addons.base.tests.common import BaseCommon


class ReportToPrinterCommon(BaseCommon):
    _test_user_groups = None
    printer_values: ClassVar[dict] = {
        "name": "Test Printer",
        "system_name": "Test Printer",
        "default": True,
        "status": "unknown",
        "status_message": "Ready",
        "model": "res.users",
        "location": "Office",
        "uri": "ipp://test-printer",
    }

    def new_printer(self, values=None):
        return self.env["printing.printer"].create(
            {**self.printer_values, **(values or {})}
        )
