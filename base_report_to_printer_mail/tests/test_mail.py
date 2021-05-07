# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.tests import common


@common.at_install(False)
@common.post_install(True)
class TestMail(common.HttpCase):
    def setUp(self):
        super(TestMail, self).setUp()
        self.Model = self.env["ir.model"]
        self.report_obj = self.env["ir.actions.report"]
        self.partner_obj = self.env["res.partner"]
        self.mail_template_obj = self.env["mail.template"]
        self.res_partner_model = self.Model.search([("model", "=", "res.partner")])
        self.server = self.env["printing.server"].create({})
        self.report_imd = self.env["ir.model.data"].create(
            {"name": "test", "module": "base_report_to_printer", "model": "ir.ui.view"}
        )
        self.report_view = self.env["ir.ui.view"].create(
            {
                "name": "Test",
                "type": "qweb",
                "xml_id": "base_report_to_printer.test",
                "model_data_id": self.report_imd.id,
                "arch": """<t t-name="base_report_to_printer.test">
                <div>Test</div>
            </t>""",
            }
        )
        self.report_imd.res_id = self.report_view.id
        self.report = self.report_obj.create(
            {
                "name": "Test",
                "report_type": "qweb-pdf",
                "model": "res.partner",
                "report_name": "base_report_to_printer.test",
            }
        )
        self.test_partner = self.partner_obj.create(
            {"name": "TestingPartner", "city": "OrigCity"}
        )
        self.email_template = self.mail_template_obj.create(
            {
                "name": "TestTemplate",
                "email_from": "myself@example.com",
                "email_to": "brigitte@example.com",
                "partner_to": "%s" % self.test_partner.id,
                "model_id": self.res_partner_model.id,
                "subject": "About ${object.name}",
                "body_html": "<p>Dear ${object.name}, "
                "your parent is ${object.parent_id and "
                'object.parent_id.name or "False"}</p>',
                "report_template": self.report.id,
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
        self.report.property_printing_action_id.action_type = "server"
        self.report.printing_printer_id = self.new_printer()
        with mock.patch(
            "odoo.addons.base_report_to_printer.models."
            "printing_printer.PrintingPrinter."
            "print_document"
        ) as print_document:
            self.email_template.generate_email(self.test_partner.id)
            print_document.assert_not_called()
