# Author: Guewen Baconnier
# Copyright 2012-2023 Camptocamp SA
# Copyright 2026 Altixia LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from io import BytesIO
from itertools import groupby

from oauthlib.oauth2.rfc6749.errors import OAuth2Error

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.modules.registry import Registry

from .pingen import APIError, NotFoundError, pingen_datetime_to_utc
from .pingen_layout import find_restricted_content

_logger = logging.getLogger(__name__)


class PingenLayoutError(UserError):
    """The PDF contains ink in a restricted printing area."""


class PingenDocument(models.Model):
    """A pingen document is the state of the synchronization of
    an attachment with pingen.com

    It stores the configuration and the current state of the synchronization.
    It also serves as a queue of documents to push to pingen.com
    """

    _name = "pingen.document"
    _description = "pingen.document"
    _inherits = {"ir.attachment": "attachment_id"}
    _order = "push_date desc, id desc"

    LAYOUT_BORDER_MM = 5.0
    LAYOUT_CORNER_MM = 15.0

    attachment_id = fields.Many2one(
        "ir.attachment", "Document", required=True, readonly=True, ondelete="cascade"
    )
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("pushed", "Pushed"),
            ("sendcenter", "In Sendcenter"),
            ("sent", "Sent"),
            ("error_undeliverable", "Undeliverable"),
            ("error", "Connection Error"),
            ("pingen_error", "Pingen Error"),
            ("canceled", "Canceled"),
        ],
        readonly=True,
        required=True,
        default="pending",
    )
    auto_send = fields.Boolean(
        help="Defines if a document is merely uploaded or also sent",
        default=True,
    )
    delivery_product = fields.Selection(
        [
            ("fast", "fast"),
            ("cheap", "cheap"),
            ("bulk", "bulk"),
            ("premium", "premium"),
            ("registered", "registered"),
            ("track", "track"),
            ("sign", "sign"),
            ("atpost_economy", "atpost_economy"),
            ("atpost_priority", "atpost_priority"),
            ("postag_a", "postag_a"),
            ("postag_b", "postag_b"),
            ("postag_b2", "postag_b2"),
            ("postag_registered", "postag_registered"),
            ("postag_aplus", "postag_aplus"),
            ("dpag_standard", "dpag_standard"),
            ("dpag_economy", "dpag_economy"),
            ("indpost_mail", "indpost_mail"),
            ("indpost_speedmail", "indpost_speedmail"),
            ("nlpost_priority", "nlpost_priority"),
            ("dhl_priority", "dhl_priority"),
        ],
        "Delivery product",
        default="cheap",
    )
    print_spectrum = fields.Selection(
        [("grayscale", "Grayscale"), ("color", "Color")],
        default="grayscale",
    )
    print_mode = fields.Selection(
        [("simplex", "Simplex"), ("duplex", "Duplex")], "Print mode", default="simplex"
    )

    push_date = fields.Datetime(readonly=True)
    # for `error` and `pingen_error` states when we push
    last_error_message = fields.Text("Error Message", readonly=True)
    # pingen API v2 fields
    pingen_uuid = fields.Char(readonly=True)
    pingen_status = fields.Char(readonly=True)
    # sendcenter infos
    parsed_address = fields.Text(readonly=True)
    cost = fields.Float(readonly=True)
    estimated_cost = fields.Float(
        readonly=True,
        help="Estimated price before sending, in the document currency.",
    )
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)
    country_id = fields.Many2one("res.country", "Country", readonly=True)
    send_date = fields.Datetime("Date of sending", readonly=True)
    pages = fields.Integer(readonly=True)
    company_id = fields.Many2one(related="attachment_id.company_id")

    _sql_constraints = [
        (
            "pingen_document_attachment_uniq",
            "unique (attachment_id)",
            "Only one Pingen document is allowed per attachment.",
        ),
    ]

    def unlink(self):
        attachments = self.attachment_id
        result = super().unlink()
        self._unlink_unused_attachments(attachments)
        return result

    @api.model
    def _unlink_unused_attachments(self, attachments):
        """Keep attachments with an owner or any stored relational reference."""
        attachments = attachments.sudo().exists()
        reference_fields = (
            self.env["ir.model.fields"]
            .sudo()
            .search(
                [
                    ("relation", "=", "ir.attachment"),
                    ("store", "=", True),
                    ("ttype", "in", ("many2one", "many2many")),
                    ("model", "!=", self._name),
                ]
            )
        )
        for attachment in attachments:
            if attachment.res_model:
                continue
            for field in reference_fields:
                if field.model not in self.env.registry:
                    continue
                model = self.env[field.model].sudo().with_context(active_test=False)
                if model.search_count([(field.name, "in", attachment.ids)]):
                    break
            else:
                attachment.exists().unlink()

    def _push_to_pingen(self, pingen=None):
        """Push a document to pingen.com
        :param Pingen pingen: optional pingen object to reuse session
        """
        decoded_document = self.attachment_id._decoded_content()
        violations = find_restricted_content(
            decoded_document,
            border_mm=self.LAYOUT_BORDER_MM,
            corner_mm=self.LAYOUT_CORNER_MM,
        )
        if violations:
            labels = {
                "top": self.env._("top margin"),
                "bottom": self.env._("bottom margin"),
                "left": self.env._("left margin"),
                "right": self.env._("right margin"),
                "bottom_left_corner": self.env._("lower-left corner"),
            }
            pages = {}
            for page, zone in violations:
                pages.setdefault(page, []).append(labels[zone])
            details = [
                self.env._(
                    "page %(page)s: %(zones)s", page=page, zones=", ".join(zones)
                )
                for page, zones in list(pages.items())[:10]
            ]
            if len(pages) > 10:
                details.append(
                    self.env._("… and %(count)s more", count=len(pages) - 10)
                )
            raise PingenLayoutError(
                self.env._(
                    "The PDF has content in areas Pingen does not print (%(areas)s). "
                    "Keep every page at least %(border)s mm from all edges and "
                    "%(corner)s mm from the lower-left corner, "
                    "then create a new document.",
                    areas="; ".join(details),
                    border=self.LAYOUT_BORDER_MM,
                    corner=self.LAYOUT_CORNER_MM,
                )
            )
        if pingen is None:
            pingen = self.company_id._get_pingen_client()
        try:
            doc_id, post_id, infos = pingen.push_document(
                self.name,
                BytesIO(decoded_document),
                self.attachment_id.mimetype,
                self.auto_send,
                self.delivery_product,
                self.print_spectrum,
                self.print_mode,
            )
        except OAuth2Error as e:
            _logger.exception(
                "Connection Error when pushing Pingen Document with ID %s to %s: %s",
                self.id,
                pingen.api_url,
                e.description,
            )
            raise
        except APIError as e:
            _logger.error(
                "API Error when pushing Pingen Document %s to %s: %s",
                self.id,
                pingen.api_url,
                str(e),
            )
            raise
        push_date = (
            pingen_datetime_to_utc(infos.get("created_at")) or fields.Datetime.now()
        )
        self.write(
            {
                "last_error_message": False,
                "state": "pushed",
                "push_date": fields.Datetime.to_string(push_date),
                "pingen_uuid": doc_id,
                "pingen_status": infos.get("status"),
            }
        )
        try:
            with self.env.cr.savepoint():
                self._refresh_letter_infos(pingen)
        except Exception:
            _logger.warning(
                "Could not refresh pushed Pingen Document %s", self.id, exc_info=True
            )
        _logger.info("Pingen Document %s: pushed to %s", self.id, pingen.api_url)

    def push_to_pingen(self):
        """Push a document to pingen.com
        Convert errors to osv.except_osv to be handled by the client.
        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        self.ensure_one()
        state = False
        error_msg = False
        try:
            session = self.company_id._get_pingen_client()
            self._push_to_pingen(pingen=session)
        except OAuth2Error:
            state = "error"
            error_msg = self.env._(
                "Connection Error when pushing document %(name)s to Pingen",
                name=self.name,
            )
        except APIError as e:
            state = "pingen_error"
            error_msg = self.env._(
                "Error when pushing the document %(name)s to Pingen:\n%(exc)s",
                name=self.name,
                exc=str(e),
            )
        except PingenLayoutError as e:
            state = "pingen_error"
            error_msg = str(e)
        except Exception as e:
            error_msg = self.env._(
                "Unexpected Error when pushing the document %(name)s to Pingen:\n"
                "%(exc)s",
                name=self.name,
                exc=str(e),
            )
            _logger.exception(error_msg)
        finally:
            if error_msg:
                vals = {"last_error_message": error_msg}
                if state:
                    vals.update({"state": state})
                # Persist the error even though the UserError below rolls back
                # the current transaction.
                with Registry(self.env.cr.dbname).cursor() as new_cr:
                    new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                    self.with_env(new_env).write(vals)

                raise UserError(error_msg)
        return True

    def _push_and_send_to_pingen_cron(self):
        """Push a document to pingen.com
        Intended to be used in a cron.
        Commit after each record
        Instead of raising, store the error in the pingen.document
        """
        with Registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            # Instead of raising, store the error in the pingen.document
            self = self.with_env(new_env)
            not_sent_docs = self.search(
                [("state", "in", ("pending", "pushed", "error"))], order="company_id"
            )
            for company, documents in groupby(not_sent_docs, lambda d: d.company_id):
                session = company._get_pingen_client()
                for document in documents:
                    if document.state == "error":
                        document._resolve_error()
                        document.invalidate_recordset()
                    try:
                        if document.state == "pending":
                            document._push_to_pingen(pingen=session)
                        elif document.state == "pushed" and not document.auto_send:
                            document._ask_pingen_send(pingen=session)
                    except OAuth2Error as e:
                        document.write({"last_error_message": e, "state": "error"})
                    except APIError as e:
                        document.write(
                            {"last_error_message": e, "state": "pingen_error"}
                        )
                    except PingenLayoutError as e:
                        document.write(
                            {"last_error_message": str(e), "state": "pingen_error"}
                        )
                    except Exception:
                        _logger.exception(
                            "Unexpected error in pingen cron for document %s",
                            document.id,
                        )
        return True

    def _resolve_error(self):
        """A document as resolved, put in the correct state"""
        if self.send_date:
            state = "sent"
        elif self.pingen_uuid:
            state = "pushed"
        else:
            state = "pending"
        self.write({"state": state})

    def resolve_error(self):
        """A document as resolved, put in the correct state"""
        for document in self:
            document._resolve_error()
        return True

    def _ask_pingen_send(self, pingen):
        """For a document already pushed to pingen, ask to send it.
        :param Pingen pingen: pingen object to reuse
        """
        try:
            infos = pingen.send_document(
                self.pingen_uuid,
                self.delivery_product,
                self.print_spectrum,
                self.print_mode,
            )
        except OAuth2Error:
            _logger.exception(
                "Connection Error when asking for sending Pingen Document %s to %s.",
                self.id,
                pingen.api_url,
            )
            raise
        except APIError:
            _logger.exception(
                "API Error when asking for sending Pingen Document %s to %s.",
                self.id,
                pingen.api_url,
            )
            raise
        self.write(
            {
                "last_error_message": False,
                "state": "sendcenter",
                "pingen_status": infos.get("status"),
            }
        )
        _logger.info(
            "Pingen Document %s: asked for sending to %s", self.id, pingen.api_url
        )
        return True

    def ask_pingen_send(self):
        """For a document already pushed to pingen, ask to send it.
        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        self.ensure_one()
        try:
            session = self.company_id._get_pingen_client()
            self._ask_pingen_send(pingen=session)
        except OAuth2Error as e:
            raise UserError(
                self.env._(
                    "Connection Error when asking for sending the document "
                    "%(name)s to Pingen",
                    name=self.name,
                )
            ) from e

        except APIError as e:
            raise UserError(
                self.env._(
                    "Error when asking Pingen to send the document %(name)s:\n"
                    "%(exc)s",
                    name=self.name,
                    exc=str(e),
                )
            ) from e

        except Exception as e:
            _logger.exception(
                "Unexpected Error when asking to send pingen.document %s", self.id
            )
            raise UserError(
                self.env._(
                    "Unexpected Error when asking to send the Document %(name)s",
                    name=self.name,
                )
            ) from e
        return True

    def _get_and_update_post_infos(self, pingen):
        """Update the informations from
        pingen of a document in the Sendcenter
        :param Pingen pingen: pingen object to reuse
        """
        self._refresh_letter_infos(pingen)

    def _refresh_letter_infos(self, pingen):
        """Read the letter and estimate its price until it has been submitted."""
        self.ensure_one()
        post_infos = self._get_post_infos(pingen)
        self._update_post_infos(post_infos)
        if (
            (post_infos.get("price_value") or 0) > 0
            or self.state in ("sendcenter", "sent", "canceled", "error_undeliverable")
            or post_infos.get("submitted_at")
        ):
            return
        # A previous estimate may no longer match the options or the letter:
        # keep amount and currency together, or clear both.
        self.write({"estimated_cost": 0.0, "currency_id": False})
        country = post_infos.get("country")
        pages = post_infos.get("file_pages")
        if not country or not isinstance(pages, int) or pages <= 0:
            return
        try:
            paper_types = post_infos.get("paper_types")
            if not isinstance(paper_types, list) or len(paper_types) != pages:
                paper_types = ["normal"] * pages
            price, currency_code = pingen.price_quote(
                country=country,
                delivery_product=self.delivery_product,
                print_mode=self.print_mode,
                print_spectrum=self.print_spectrum,
                paper_types=paper_types,
            )
            if price is not None:
                with self.env.cr.savepoint():
                    currency = (
                        self.env["res.currency"]
                        .with_context(active_test=False)
                        .search([("name", "=", currency_code)], limit=1)
                    )
                    self.write({"estimated_cost": price, "currency_id": currency.id})
        except Exception:
            _logger.warning(
                "Could not estimate Pingen Document %s", self.id, exc_info=True
            )

    def _get_post_infos(self, pingen):
        if not self.pingen_uuid:
            return {}
        try:
            post_infos = pingen.post_infos(self.pingen_uuid)
        except OAuth2Error:
            _logger.exception(
                "Connection Error when getting infos of Pingen Document %s from %s.",
                self.id,
                pingen.api_url,
            )
            raise
        except NotFoundError:
            _logger.info("Pingen letter for Document %s no longer exists", self.id)
            raise
        except APIError:
            _logger.exception(
                "API Error when getting infos of Pingen Document %s from %s.",
                self.id,
                pingen.api_url,
            )
            raise
        return post_infos or {}

    # Pingen letter statuses that settle the Odoo state. Pingen does not
    # publish an exhaustive list; any other status only updates pingen_status.
    _PINGEN_STATUS_TO_STATE = {
        "sent": "sent",
        "delivered": "sent",
        "undeliverable": "error_undeliverable",
        "cancelled": "canceled",
        "canceled": "canceled",
    }

    @api.model
    def _prepare_values_from_post_infos(self, post_infos):
        post_infos = post_infos or {}
        country = self.env["res.country"]
        if post_infos.get("country"):
            country = country.search([("code", "=", post_infos["country"])], limit=1)
        currency = self.env["res.currency"]
        if post_infos.get("price_currency"):
            currency = currency.with_context(active_test=False).search(
                [("name", "=", post_infos["price_currency"])], limit=1
            )
        vals = {
            "pingen_status": post_infos.get("status"),
            "parsed_address": post_infos.get("address"),
            "country_id": country.id,
            "pages": post_infos.get("file_pages"),
            "last_error_message": False,
            "cost": post_infos.get("price_value") or 0.0,
            "currency_id": currency.id,
        }
        state = self._PINGEN_STATUS_TO_STATE.get(post_infos.get("status"))
        if state:
            vals["state"] = state
        send_date = False
        if state == "sent":
            post_date = pingen_datetime_to_utc(post_infos.get("submitted_at"))
            send_date = fields.Datetime.to_string(post_date) if post_date else False
        vals["send_date"] = send_date
        return vals

    def _update_post_infos(self, post_infos):
        self.ensure_one()
        values = self._prepare_values_from_post_infos(post_infos)
        self.write(values)
        _logger.info("Pingen Document %s: status updated", self.id)

    def _update_post_infos_cron(self):
        """Refresh unsettled letters and remove confirmed missing letters.

        API and authentication failures are retried on the next daily run.
        """
        with Registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            self = self.with_env(new_env)
            # Only letters that reached pingen.com and are not settled yet.
            pushed_docs = self.search(
                [
                    ("pingen_uuid", "!=", False),
                    ("state", "not in", ("sent", "canceled", "error_undeliverable")),
                ]
            )
            reachable_by_company = {}
            for document in pushed_docs:
                session = document.company_id._get_pingen_client()
                try:
                    document._get_and_update_post_infos(pingen=session)
                except NotFoundError:
                    company_id = document.company_id.id
                    if company_id not in reachable_by_company:
                        reachable_by_company[company_id] = (
                            session.organisation_reachable()
                        )
                    if reachable_by_company[company_id]:
                        _logger.info(
                            "Removing Pingen Document %s: letter deleted on Pingen",
                            document.id,
                        )
                        document.unlink()
                    else:
                        _logger.warning(
                            "Keeping Pingen Document %s: organisation unreachable",
                            document.id,
                        )
                # pylint: disable=W7938
                # pylint: disable=W8138
                except (OAuth2Error, APIError):
                    # will be retried the next time
                    # In any case, the error has been
                    # logged by _get_post_infos
                    pass
        return True

    def _refresh_pushed_documents_cron(self):
        """Refresh uploaded letters independently; retry failures on the next run."""
        try:
            with Registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                documents = self.with_env(new_env).search([("state", "=", "pushed")])
                for document in documents:
                    try:
                        with new_cr.savepoint():
                            session = document.company_id._get_pingen_client()
                            document._refresh_letter_infos(session)
                    except Exception:
                        _logger.warning(
                            "Could not refresh Pingen Document %s in cron",
                            document.id,
                            exc_info=True,
                        )
        except Exception:
            _logger.warning("Could not refresh pushed Pingen letters", exc_info=True)
        return True

    def update_post_infos(self):
        """Update the informations from pingen of a document in the Sendcenter
        Wrapper method for multiple ids (when triggered from button for
        instance) for public interface.
        """
        self.ensure_one()
        try:
            session = self.company_id._get_pingen_client()
            self._get_and_update_post_infos(pingen=session)
        except OAuth2Error as e:
            raise UserError(
                self.env._(
                    "Connection Error when updating the status of Document "
                    "%(name)s from Pingen",
                    name=self.name,
                )
            ) from e
        except NotFoundError as e:
            raise UserError(
                self.env._(
                    "This letter no longer exists on Pingen. "
                    "It will be removed by the daily update."
                )
            ) from e
        except APIError as e:
            raise UserError(
                self.env._(
                    "Error when updating the status of Document %(name)s from "
                    "Pingen:\n%(exc)s",
                    name=self.name,
                    exc=str(e),
                )
            ) from e
        except Exception as e:
            _logger.exception(
                "Unexpected Error when updating the status of pingen.document %s",
                self.id,
            )
            raise UserError(
                self.env._(
                    "Unexpected Error when updating the status of Document %(name)s",
                    name=self.name,
                )
            ) from e
        return True
