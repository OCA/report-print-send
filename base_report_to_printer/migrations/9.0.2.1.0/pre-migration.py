# -*- coding: utf-8 -*-
# Copyright 2016 ADHOC SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(cr, version):
    # fix that afip should be no updatable
    openupgrade.logged_query(cr, """
        UPDATE ir_model_data set noupdate=False
        WHERE
            module = 'base_report_to_printer' AND
            model in ('ir.model.access', 'res.groups')
        """)
