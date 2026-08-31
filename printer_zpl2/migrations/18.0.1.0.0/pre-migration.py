# Copyright 2026 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    view = env.ref(
        "printer_zpl2.act_open_printing_label_zpl2_view_tree", raise_if_not_found=False
    )
    view.unlink()
