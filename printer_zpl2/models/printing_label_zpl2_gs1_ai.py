from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PrintingLabelZpl2Gs1AI(models.Model):
    _name = "printing.label.zpl2.gs1.ai"
    _description = "GS1-128 Application Identifier Configuration"
    _order = "sequence"

    component_id = fields.Many2one(
        "printing.label.zpl2.component",
        string="Label Component",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    ai = fields.Selection(
        [
            ("00", "SSCC"),
            ("01", "GTIN"),
            ("10", "Batch/Lot Number"),
            ("11", "Production Date (YYMMDD)"),
            ("13", "Packaging Date (YYMMDD)"),
            ("15", "Best Before Date (YYMMDD)"),
            ("17", "Expiration Date (YYMMDD)"),
            ("21", "Serial Number"),
            ("30", "Count"),
            ("310n", "Net Weight (kg)"),  # n = decimal places
            ("320n", "Net Weight (lbs)"),  # n = decimal places
        ],
        string="Application Identifier",
        required=True,
    )
    field_name = fields.Char(
        string="Field Path",
        required=True,
        help="Field name or dot-notation path (e.g. product_id.weight)",
    )
    uom_field_name = fields.Char(
        string="UoM Field Path",
        help="Field path to the UoM field (e.g. product_id.uom_id)",
    )
    decimal_places = fields.Integer(
        help="For weight AIs (310n, 320n), specify decimal places (0-5)",
    )

    @api.constrains("field_name", "uom_field_name")
    def _check_field_paths(self):
        for record in self:
            if not record.field_name:
                continue

            model = record.component_id.model_id.model
            Model = self.env[model]

            # Check field_name path
            self._check_field_path(Model, record.field_name)

            # Check uom_field_name path if weight AI
            if record.ai.startswith(("310", "320")) and record.uom_field_name:
                self._check_field_path(Model, record.uom_field_name)

    def _check_field_path(self, Model, field_path):
        field_path = field_path.split(".")
        current = Model

        try:
            for field in field_path[:-1]:
                field_def = current._fields[field]
                if not field_def.type == "many2one":
                    raise ValidationError(
                        _(
                            "Field %(field)s in path %(path)s is not a relational field",
                            field=field,
                            path=".".join(field_path),
                        )
                    )
                current = self.env[field_def.comodel_name]

            if field_path[-1] not in current._fields:
                raise ValidationError(
                    _(
                        "Field %(field)s does not exist on model %(model)s",
                        field=field_path[-1],
                        model=current._name,
                    )
                )
        except KeyError:
            raise ValidationError(
                _("Invalid field path: %(path)s", path=".".join(field_path))
            ) from None

    def _format_gs1_value(self, record):
        """Format field value according to GS1 AI rules"""
        # Handle dot notation for related fields
        field_path = self.field_name.split(".")
        value = record
        for field_name in field_path:
            value = value[field_name] if value else False

        if not value:
            return False, False  # Return False to indicate this AI should be skipped
        try:
            ai, value = getattr(self, f"_format_gs1_ai{self.ai}")(value, record)
        except AttributeError:
            ai = self.ai

        return ai, str(value)

    def _format_gs1_ai00(self, value, record):
        """Format value for GS1-128 AI 00"""
        return self.ai, f"{int(value):018d}"

    def _format_gs1_ai01(self, value, record):
        """Format value for GS1-128 AI 01"""
        return self.ai, f"{int(value):014d}"

    def _format_gs1_ai10(self, value, record):
        """Format value for GS1-128 AI 10"""
        return self.ai, value[:20]

    def _format_gs1_ai11(self, value, record):
        """Format value for GS1-128 AI 11"""
        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d")
        return self.ai, value.strftime("%y%m%d")

    _format_gs1_ai13 = _format_gs1_ai11
    _format_gs1_ai15 = _format_gs1_ai11
    _format_gs1_ai17 = _format_gs1_ai11

    def _format_gs1_ai21(self, value, record):
        return self.ai, value

    def _format_gs1_ai30(self, value, record):
        return self.ai, value

    def _format_gs1_ai310n(self, value, record):
        target_uom = self.env.ref("uom.product_uom_kgm")
        return self._format_gs1_weight(value, target_uom, record)

    def _format_gs1_ai320n(self, value, record):
        target_uom = self.env.ref("uom.product_uom_lb")
        return self._format_gs1_weight(value, target_uom, record)

    def _format_gs1_weight(self, value, target_uom, record):
        source_uom = None
        if self.uom_field_name:
            source_uom = record
            for field_name in self.uom_field_name.split("."):
                source_uom = source_uom[field_name] if source_uom else False
            if source_uom:
                value = self._convert_weight(value, source_uom, target_uom)
        value = int(round(value, self.decimal_places) * 10**self.decimal_places)
        return self.ai.replace("n", str(self.decimal_places)), f"{value:06d}"

    def _convert_weight(self, value, from_uom, to_uom):
        try:
            return from_uom._compute_quantity(value, to_uom)
        except Exception:
            raise ValidationError(
                _(
                    "Failed to convert weight from %(from_uom)s to %(to_uom)s",
                    from_uom=from_uom.name,
                    to_uom=to_uom.name,
                )
            ) from None
