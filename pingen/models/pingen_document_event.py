# Copyright 2026 Altixia LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .pingen import pingen_datetime_to_utc


class PingenDocumentEvent(models.Model):
    _name = "pingen.document.event"
    _description = "Pingen Document Event"
    # An event without a date must not hide the newest ones.
    _order = "emitted_at desc nulls last, id desc"
    _rec_name = "name"

    document_id = fields.Many2one(
        "pingen.document", required=True, ondelete="cascade", index=True, readonly=True
    )
    company_id = fields.Many2one(
        related="document_id.company_id", store=True, index=True
    )
    pingen_uuid = fields.Char("Pingen Event ID", required=True, readonly=True)
    code = fields.Char(readonly=True)
    name = fields.Char(readonly=True)
    label = fields.Char("Event", compute="_compute_label", readonly=True)
    producer = fields.Char(readonly=True)
    location = fields.Char(readonly=True)
    details = fields.Text(readonly=True)
    emitted_at = fields.Datetime("Date", readonly=True)

    _sql_constraints = [
        (
            "document_event_uuid_uniq",
            "unique (document_id, pingen_uuid)",
            "A Pingen event must be unique per document.",
        ),
    ]

    @api.model
    def _event_labels(self):
        return {
            "created": self.env._("PDF received"),
            "content_passed_inspection": self.env._("Validation passed"),
            "content_failed_inspection": self.env._("Validation failed"),
            "submitted": self.env._("Submitted"),
            "processing": self.env._("Processing"),
            "accepted": self.env._("Sending accepted"),
            "transferred_to_printcenter": self.env._("Transferred for printing"),
            "transferred_to_distributor": self.env._("Handed to distributor"),
            "track_and_trace": self.env._("Track & Trace"),
        }

    @api.depends("code", "name")
    @api.depends_context("lang")
    def _compute_label(self):
        labels = self._event_labels()
        for event in self:
            event.label = labels.get(event.code) or event.name or event.code

    @api.model
    def _prepare_values_from_node(self, node):
        attributes = node.get("attributes") if isinstance(node, dict) else None
        if not isinstance(attributes, dict):
            attributes = {}
        values = {
            key: (attributes[key] or False)
            if isinstance(attributes.get(key), str)
            else False
            for key in ("code", "name", "producer", "location")
        }
        data = attributes.get("data")
        values["details"] = (
            "\n".join(item for item in data if isinstance(item, str)) or False
            if isinstance(data, list)
            else False
        )
        emitted_at = attributes.get("emitted_at")
        try:
            values["emitted_at"] = (
                pingen_datetime_to_utc(emitted_at) or False
                if isinstance(emitted_at, str)
                else False
            )
        except (ValueError, TypeError, OverflowError, OSError):
            values["emitted_at"] = False
        return values
