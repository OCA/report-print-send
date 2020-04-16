from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return
    if not openupgrade.table_exists(cr, 'printing_tray_input'):
        openupgrade.rename_tables(cr, [('printing_tray', 'printing_tray_input')])
        openupgrade.rename_models(cr, [
            ('printing.tray', 'printing.tray.input'),
        ])
