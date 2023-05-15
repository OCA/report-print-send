from odoo import api, fields, models


class PrintConfig(models.Model):
    _name = "print.config"
    _inherit = ["mail.thread"]
    _description = "Simple Printing Configuration"
    _rec_names_search = ["server", "company_id"]
    _check_company_auto = True

    server = fields.Char(
        string="🖥 Server",
        required=True,
        tracking=True,
        help="IP or name resolved by your internal DNS",
    )
    port = fields.Integer(tracking=True)
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    display_name = fields.Char("Name", compute="_compute_display_name", store=True)
    comment = fields.Char()
    printer_ids = fields.One2many(comodel_name="printer", inverse_name="config_id")

    @api.depends("server", "company_id")
    def _compute_display_name(self):
        for rec in self:
            company = rec.company_id
            if company:
                rec.display_name = "{} ({})".format(rec.server, company.name)
            else:
                rec.display_name = rec.server
