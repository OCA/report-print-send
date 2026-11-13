# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo.tests import tagged
from odoo.tests.common import HttpCase

test_xml_id = "base_report_to_printer.test"


@tagged("post_install", "-at_install")
class TestMail(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Model = cls.env["ir.model"]
        cls.report_obj = cls.env["ir.actions.report"]
        cls.partner_obj = cls.env["res.partner"]
        cls.mail_template_obj = cls.env["mail.template"]
        cls.res_partner_model = cls.Model.search([("model", "=", "res.partner")])
        cls.server = cls.env["printing.server"].create({})
        cls.report_imd = cls.env["ir.model.data"].create(
            {"name": "test", "module": "base_report_to_printer", "model": "ir.ui.view"}
        )
        cls.report_view = cls.env["ir.ui.view"].create(
            {
                "name": "Test",
                "type": "qweb",
                "xml_id": test_xml_id,
                "model_data_id": cls.report_imd.id,
                "arch": f"""<t t-name="{test_xml_id}">
                <div>Test</div>
            </t>""",
            }
        )
        cls.report_imd.res_id = cls.report_view.id
        cls.report = cls.report_obj.create(
            {
                "name": "Test",
                "report_type": "qweb-pdf",
                "model": "res.partner",
                "report_name": test_xml_id,
            }
        )
        cls.test_partner = cls.partner_obj.create(
            {"name": "TestingPartner", "city": "OrigCity"}
        )
        cls.email_template = cls.mail_template_obj.create(
            {
                "name": "TestTemplate",
                "email_from": "mycls@example.com",
                "email_to": "brigitte@example.com",
                "partner_to": str(cls.test_partner.id),
                "model_id": cls.res_partner_model.id,
                "subject": "About ${object.name}",
                "body_html": "<p>Dear ${object.name}, "
                "your parent is ${object.parent_id and "
                'object.parent_id.name or "False"}</p>',
                "report_template_ids": [(4, cls.report.id)],
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

    def test_generate_email(self):
        """
        It should NOT print the report,
        regardless of the defined behaviour
        """
        self.assertEqual(self.report_view.xml_id, test_xml_id)
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_printer()

        with mock.patch(
            "odoo.addons.base_report_to_printer.models."
            "printing_printer.PrintingPrinter."
            "print_document"
        ) as print_document:
            self.email_template._generate_template(
                [self.test_partner.id],
                render_fields=[
                    "name",
                    "email_from",
                    "email_to",
                    "partner_to",
                    "subject",
                    "body_html",
                ],
            )
            print_document.assert_not_called()
