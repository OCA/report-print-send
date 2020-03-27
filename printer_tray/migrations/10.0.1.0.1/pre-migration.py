# -*- coding: utf-8 -*-

from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return
    openupgrade.rename_tables(cr, [('printing_tray', 'printing_tray_input')])
    openupgrade.rename_models(cr, [
        ('printing.tray', 'printing.tray.input'),
    ])
