import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Printer(models.Model):
    _name = "printer"
    _description = "Printers belongs to a printer server address attached "
    "to a company or a warehouse"

    name = fields.Char(required=True, help="must be completed by internal user")
    usage = fields.Char(
        required=True,
        help="Developers may use this to guess adapted printers for their workflows",
    )
    comment = fields.Char()
    config_id = fields.Many2one(comodel_name="print.config", required=True)
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse")
    readonly = fields.Boolean(
        help="Make some fields readonly in views if set to True.\n"
        "In some case, erp project may be imply minimal config as module data\n"
        "with some fields might updated within the interface"
    )
    company_id = fields.Many2one(
        "res.company",
        related="config_id.company_id",
        store=True,
    )

    @api.model
    def _get_printer_by_usage(self):
        printers = {}
        company = self.env.company

        domain = [("company_id", "=", company.id)]
        if self.env.user.property_warehouse_id:
            domain.append(("warehouse_id", "=", self.env.user.property_warehouse_id.id))
        else:
            domain.append(("warehouse_id", "=", False))

        for device in self.search(domain, order="warehouse_id DESC, usage, name DESC"):
            conf = device.sudo().config_id
            printers[device.usage] = {
                "location": "https://%s:%s" % (conf.server, conf.port or 0),
                "name": device.name,
                "comment": device.comment,
            }
        _logger.info(" >>> Printers %s" % printers)
        if not printers:
            raise UserError(
                _("There is no printer accessible to you in the company %s")
                % company.name
            )
        return printers
