# Copyright 2026 Altixia LLC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api

# Scheduled actions created by 18.0.1.0.0 referenced their method without
# calling it. Only these exact expressions are repaired; customized code is kept.
BROKEN_CODE = {
    "pingen.ir_cron_push_pingen": "model._push_and_send_to_pingen_cron",
    "pingen.ir_cron_update_pingen": "model._update_post_infos_cron",
    "pingen.ir_cron_refresh_pingen_pushed": "model._refresh_pushed_documents_cron",
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, broken in BROKEN_CODE.items():
        cron = env.ref(xmlid, raise_if_not_found=False)
        if cron and (cron.code or "").strip() == broken:
            cron.code = broken + "()"
    update_cron = env.ref("pingen.ir_cron_update_pingen", raise_if_not_found=False)
    if update_cron:
        update_cron.active = True
