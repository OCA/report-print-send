from odoo import fields, models


def setup_test_model(env, model_cls):
    """Pass a test model class and initialize it.

    Courtesy of SBidoul from https://github.com/OCA/mis-builder :)
    """
    model_cls._build_model(env.registry, env.cr)
    env.registry.setup_models(env.cr)
    env.registry.init_models(
        env.cr, [model_cls._name], dict(env.context, update_custom_fields=True)
    )


def teardown_test_model(env, model_cls):
    """Pass a test model class and deinitialize it.

    Courtesy of SBidoul from https://github.com/OCA/mis-builder :)
    """
    if not getattr(model_cls, "_teardown_no_delete", False):
        del env.registry.models[model_cls._name]
    env.registry.setup_models(env.cr)


class PrintingAutoTesterChild(models.Model):
    _name = "printingauto.tester.child"

    name = fields.Char()


class PrintingAutoTester(models.Model):
    _name = "printingauto.tester"
    _inherit = "printing.auto.mixin"

    name = fields.Char()
    child_ids = fields.Many2many("printingauto.tester.child")
