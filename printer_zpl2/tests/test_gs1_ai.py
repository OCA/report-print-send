# Copyright 2024 Your Company
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPrintingLabelZpl2Gs1AI(TransactionCase):
    def setUp(self):
        super().setUp()
        self.server = self.env["printing.server"].create({})
        self.printer = self.env["printing.printer"].create(
            {
                "name": "Test Printer",
                "server_id": self.server.id,
                "system_name": "Test",
                "default": True,
                "status": "unknown",
                "status_message": "Ready",
                "model": "res.users",
                "location": "Office",
                "uri": "URI",
            }
        )

        # Create a test product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "default_code": "TEST001",
                "barcode": "12345678",
                "weight": 1.23,
            }
        )

        # Create a label
        self.label = self.env["printing.label.zpl2"].create(
            {
                "name": "GS1-128 Test Label",
                "model_id": self.env.ref("product.model_product_product").id,
            }
        )

        # Create a GS1-128 component
        self.component = self.env["printing.label.zpl2.component"].create(
            {
                "name": "GS1-128 Component",
                "label_id": self.label.id,
                "component_type": "gs1_128",
            }
        )

    def test_gs1_ai_validation(self):
        """Test validation of GS1 AI configuration"""
        # Test valid field path
        ai = self.env["printing.label.zpl2.gs1.ai"].create(
            {
                "component_id": self.component.id,
                "ai": "01",
                "field_name": "barcode",
            }
        )
        self.assertTrue(ai)

        # Test invalid field path
        with self.assertRaises(ValidationError):
            self.env["printing.label.zpl2.gs1.ai"].create(
                {
                    "component_id": self.component.id,
                    "ai": "01",
                    "field_name": "nonexistent_field",
                }
            )

    def test_gs1_ai_formatting(self):
        """Test formatting of different GS1 AIs"""
        Gs1AI = self.env["printing.label.zpl2.gs1.ai"]

        # Test GTIN (AI 01)
        ai = Gs1AI.create(
            {
                "component_id": self.component.id,
                "ai": "01",
                "field_name": "barcode",
            }
        )
        ai_code, value = ai._format_gs1_value(self.product)
        self.assertEqual(ai_code, "01")
        self.assertEqual(value, "00000012345678")

        # Test Weight (AI 310n)
        ai = Gs1AI.create(
            {
                "component_id": self.component.id,
                "ai": "310n",
                "field_name": "weight",
                "decimal_places": 3,
            }
        )
        ai_code, value = ai._format_gs1_value(self.product)
        self.assertEqual(ai_code, "3103")
        self.assertEqual(value, "001230")  # 1.23 kg with 3 decimal places

        # Test Date (AI 11)
        ai = Gs1AI.create(
            {
                "component_id": self.component.id,
                "ai": "11",
                "field_name": "create_date",
            }
        )
        ai_code, value = ai._format_gs1_value(self.product)
        self.assertEqual(ai_code, "11")
        self.assertEqual(value, self.product.create_date.strftime("%y%m%d"))

    def test_gs1_ai_sequence(self):
        """Test GS1 AI sequencing"""
        Gs1AI = self.env["printing.label.zpl2.gs1.ai"]

        # Create AIs in non-sequential order
        ai2 = Gs1AI.create(
            {
                "component_id": self.component.id,
                "ai": "01",
                "field_name": "barcode",
                "sequence": 20,
            }
        )
        ai1 = Gs1AI.create(
            {
                "component_id": self.component.id,
                "ai": "10",
                "field_name": "barcode",
                "sequence": 10,
            }
        )

        # Check ordering
        ais = self.component.gs1_ai_ids.sorted()
        self.assertEqual(ais[0], ai1)
        self.assertEqual(ais[1], ai2)

    def test_gs1_weight_uom_conversion(self):
        """Test weight UoM conversion for GS1 AIs"""
        # Create a product with weight in pounds
        lb_uom = self.env.ref("uom.product_uom_lb")
        product_lb = self.env["product.product"].create(
            {
                "name": "Test Product (lb)",
                "type": "product",
                "weight": 2.2,  # 2.2 lbs ≈ 1 kg
                "uom_id": lb_uom.id,
                "uom_po_id": lb_uom.id,  # Purchase UoM must be in same category as uom_id
            }
        )

        # Test weight conversion to kg (AI 310n)
        ai = self.env["printing.label.zpl2.gs1.ai"].create(
            {
                "component_id": self.component.id,
                "ai": "310n",
                "field_name": "weight",
                "uom_field_name": "uom_id",
                "decimal_places": 3,
            }
        )
        ai_code, value = ai._format_gs1_value(product_lb)
        self.assertEqual(ai_code, "3103")
        # 2.2 lbs ≈ 1 kg, formatted with 3 decimal places
        self.assertEqual(value, "001000")

    def test_gs1_ai_field_validation_errors(self):
        """Test field validation error cases"""
        # Test invalid relational field type
        with self.assertRaises(ValidationError):
            self.env["printing.label.zpl2.gs1.ai"].create(
                {
                    "component_id": self.component.id,
                    "ai": "01",
                    "field_name": "name.invalid",  # name is char, not many2one
                }
            )

        # Test non-existent field in path
        with self.assertRaises(ValidationError):
            self.env["printing.label.zpl2.gs1.ai"].create(
                {
                    "component_id": self.component.id,
                    "ai": "01",
                    "field_name": "product_id.nonexistent",
                }
            )

    def test_gs1_ai_empty_values(self):
        """Test handling of empty/false values"""
        Gs1AI = self.env["printing.label.zpl2.gs1.ai"]

        # Test with empty field value
        self.product.barcode = False
        ai = Gs1AI.create(
            {
                "component_id": self.component.id,
                "ai": "01",
                "field_name": "barcode",
            }
        )
        result = ai._format_gs1_value(self.product)
        self.assertFalse(result[1])  # Should return False for empty values

        # Test component data generation with empty value
        self.env["printing.label.zpl2.gs1.ai"].create(
            [
                {
                    "component_id": self.component.id,
                    "sequence": 10,
                    "ai": "01",
                    "field_name": "barcode",  # Empty value
                },
                {
                    "component_id": self.component.id,
                    "sequence": 20,
                    "ai": "310n",
                    "field_name": "weight",  # Has value
                    "decimal_places": 3,
                },
            ]
        )

        # Only the weight AI should appear in the data
        data = self.component._generate_gs1_128_data(self.product)
        self.assertNotIn("(01)", data)  # Empty barcode AI should be skipped
        self.assertIn("(3103)001230", data)  # Weight AI should be included

    def test_gs1_ai_weight_conversion_errors(self):
        """Test weight conversion error handling"""
        # Create incompatible UoMs
        volume_uom = self.env.ref("uom.product_uom_litre")
        weight_uom = self.env.ref("uom.product_uom_kgm")

        # Try to convert between incompatible UoMs
        ai = self.env["printing.label.zpl2.gs1.ai"].create(
            {
                "component_id": self.component.id,
                "ai": "310n",
                "field_name": "weight",
                "decimal_places": 3,
            }
        )

        with self.assertRaises(ValidationError):
            ai._convert_weight(1.0, volume_uom, weight_uom)

    def test_gs1_ai_date_formatting(self):
        """Test date field formatting"""
        Gs1AI = self.env["printing.label.zpl2.gs1.ai"]
        now = datetime.now().strftime("%y%m%d")
        ai = Gs1AI.create(
            {
                "component_id": self.component.id,
                "ai": "11",
                "field_name": "create_date",
            }
        )
        ai_code, value = ai._format_gs1_value(self.product)
        self.assertEqual(ai_code, "11")
        self.assertEqual(value, now)

        # Test with another date AI
        ai = Gs1AI.create(
            {
                "component_id": self.component.id,
                "ai": "13",  # Packaging date
                "field_name": "create_date",
            }
        )
        ai_code, value = ai._format_gs1_value(self.product)
        self.assertEqual(ai_code, "13")
        self.assertEqual(value, now)

    def test_gs1_ai_sscc_formatting(self):
        """Test SSCC number formatting"""
        self.product.barcode = "123456789012345675"
        ai = self.env["printing.label.zpl2.gs1.ai"].create(
            {
                "component_id": self.component.id,
                "ai": "00",
                "field_name": "barcode",
            }
        )
        ai_code, value = ai._format_gs1_value(self.product)
        self.assertEqual(ai_code, "00")
        self.assertEqual(value, "123456789012345675")

    def test_gs1_ai_component_data_generation(self):
        """Test GS1-128 component data generation"""
        # Create multiple AIs
        self.env["printing.label.zpl2.gs1.ai"].create(
            [
                {
                    "component_id": self.component.id,
                    "sequence": 10,
                    "ai": "01",
                    "field_name": "barcode",
                },
                {
                    "component_id": self.component.id,
                    "sequence": 20,
                    "ai": "310n",
                    "field_name": "weight",
                    "decimal_places": 3,
                },
            ]
        )

        # Test data generation
        data = self.component._generate_gs1_128_data(self.product)
        self.assertIn("(01)00000012345678", data)
        self.assertIn("(3103)001230", data)
