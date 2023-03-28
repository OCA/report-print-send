# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from . import models

def _post_init_pingen_env(cr,registry):
    # When installing pingen_env we want to delete data from DB
    cr.execute("""UPDATE res_company
        SET pingen_clientid = NULL, 
        pingen_client_secretid = NULL, 
        pingen_organization = NULL, 
        pingen_staging = NULL,
        pingen_webhook_secret = NULL
        """)
