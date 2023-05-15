from odoo import fields, models


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
