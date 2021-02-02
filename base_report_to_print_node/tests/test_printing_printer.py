##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo.tests.common import TransactionCase


class TestPrintingPrinter(TransactionCase):
    def setUp(self):
        super(TestPrintingPrinter, self).setUp()

        # we set the api key, this value does not really exist is just for the
        # mock process
        
        # api_key = self.env["ir.config_parameter"].sudo().get_param("base_report_to_print_node.api_key")

        # if not api_key:
        #     dummy, action_id = self.env["ir.model.data"].get_object_reference(
        #         "base_setup", "action_general_configuration"
        #     )
        #     msg = _("You haven't configured your 'Print Node Api Key'.")
        #     raise RedirectWarning(msg, action_id, _("Go to the configuration panel"))

    def test_00_verify_apikey_exist(self):
        """ Verify that the API key exist if not api key then raise error"""
        api_key = self.env["ir.config_parameter"].sudo().get_param("base_report_to_print_node.api_key")
        self.assertTrue(api_key)

    def test_01_create_printer(self):
        pass

    def test_03_verify_printer_status(self):
        pass

    def test_04_print_job(self):
        pass
