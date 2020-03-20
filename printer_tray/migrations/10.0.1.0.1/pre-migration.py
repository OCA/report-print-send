# -*- coding: utf-8 -*-

from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    openupgrade.rename_models(cr, [
        ('printing.tray', 'printing.tray.input'),
    ])
