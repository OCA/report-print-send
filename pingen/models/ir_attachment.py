# Author: Guewen Baconnier
# Copyright 2012-2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    send_to_pingen = fields.Boolean("Send to Pingen.com")
    pingen_document_ids = fields.One2many(
        "pingen.document", "attachment_id", string="Pingen Document", readonly=True
    )

    def _prepare_pingen_document_vals(self):
        return {
            "attachment_id": self.id,
        }

    def _handle_pingen_document(self):
        """Reponsible of the related ``pingen.document``
        when the ``send_to_pingen``
        field is modified.
        Only one pingen document can be created per attachment.
        When ``send_to_pingen`` is activated:
          * Create a ``pingen.document`` if it does not already exist
          * Put the related ``pingen.document`` to ``pending``
            if it already exist
        When it is deactivated:
          * Do nothing if no related ``pingen.document`` exists
          * Or cancel it
          * If it has already been pushed to pingen.com, raises
            an `osv.except_osv` exception
        """
        pingen_document_obj = self.env["pingen.document"]
        document = self.pingen_document_ids[0] if self.pingen_document_ids else None
        if self.send_to_pingen:
            if document:
                document.write({"state": "pending"})
            else:
                pingen_document_obj.create(self._prepare_pingen_document_vals())
        else:
            if document:
                if document.state == "pushed":
                    raise UserError(
                        self.env._(
                            "Error. The attachment %(name)s is already pushed to "
                            "pingen.com.",
                            name=self.name,
                        )
                    )
                document.write({"state": "canceled"})
        return

    @api.model_create_multi
    def create(self, vals_list):
        attachments = super().create(vals_list)
        for attachment, vals in zip(attachments, vals_list, strict=True):
            if "send_to_pingen" in vals:
                attachment._handle_pingen_document()
        return attachments

    def write(self, vals):
        res = super().write(vals)
        if "send_to_pingen" in vals:
            for attachment in self:
                attachment._handle_pingen_document()
        return res

    def _decoded_content(self):
        """Returns the decoded content of an attachment (stored or url)
        Returns None if the type is 'url' and the url is not reachable.
        """
        decoded_document = None
        if self.type == "binary":
            decoded_document = base64.b64decode(self.datas)
        elif self.type == "url":
            response = requests.get(self.url, timeout=30)
            if response.ok:
                decoded_document = response.content
        else:
            raise UserError(
                self.env._(
                    "The type of attachment %(type)s is not handled", type=self.type
                )
            )
        return decoded_document
