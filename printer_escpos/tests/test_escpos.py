# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import mock

from odoo.tests.common import TransactionCase

model = "odoo.addons.base_report_to_printer.models.printing_server"


class TestEscpos(TransactionCase):
    def setUp(self):
        super().setUp()
        self.escpos = self.env["printing.escpos"].create(
            {
                "name": "Partner ticket",
                "model_id": self.env.ref("base.model_res_partner").id,
                "mode": "arch",
                "arch": """
            <receipt>
                <t t-foreach="docs" t-as="doc">
                    <h1 t-esc="doc.name"/>
                    <div t-esc="'Bigger %s' % doc.name"
                    width="3" height="3" custom_size="1"/>
                    <h2>Subtitle L2</h2>
                    <h3>Subtitle L3</h3>
                    <h4>Subtitle L4</h4>
                    <h5>Subtitle L5</h5>
                    <div>Text with font A</div>
                    <div font="b">Text with font B</div>
                    <div bold="1">Text in bold</div>
                    <div underline="1">Text underlined</div>
                    <line>
                        <left>Product</left>
                        <right>0.15€</right>
                    </line>
                    <hr />
                    <line size='double-height'>
                        <left>TOTAL</left>
                        <right>0.15€</right>
                    </line>
                    <barcode encoding='ean13'>
                        5449000000996
                    </barcode>
                    <qr qrsize="4" align="center">This is a QR</qr>
                    <cashdraw />
                    <cut />
                </t>
            </receipt>
            """,
            }
        )
        self.server = self.env["printing.server"].create({})
        self.printer = self.env["printing.printer"].create(
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

    @mock.patch("%s.cups" % model)
    def test_print_ticket(self, cups):
        """Check that printing an empty label works"""
        self.escpos.print_escpos(self.printer, self.env.user.partner_id)
        cups.Connection().printFile.assert_called_once()

    @mock.patch("%s.cups" % model)
    def test_print_ticket_wizard(self, cups):
        """Check that printing an empty label works"""
        self.env["print.record.escpos"].with_context(
            active_model="res.partner", active_ids=self.env.user.partner_id.ids
        ).create(
            {
                "printer_id": self.printer.id,
                "escpos_id": self.escpos.id,
            }
        ).print_escpos()
        cups.Connection().printFile.assert_called_once()

    @mock.patch("%s.cups" % model)
    def test_print_ticket_test(self, cups):
        """Check that printing an empty label works"""
        self.escpos.write(
            {
                "test_print_mode": True,
                "printer_id": self.printer.id,
                "record_id": self.env.user.partner_id.id,
            }
        )
        self.escpos.print_test_escpos()
        cups.Connection().printFile.assert_called_once()
