from openerp.osv import osv, fields

class MailTemplate(osv.osv):
    _inherit = "email.template"

    def generate_email(self, cr, uid, template_id, res_id, context=None):
        if context is None:
            context = {}
        context.update({'must_skip_send_to_printer': True})
        return super(MailTemplate, self).generate_email(cr, uid, template_id, res_id, context)
