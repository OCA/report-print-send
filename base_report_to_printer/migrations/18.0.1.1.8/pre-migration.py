from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.table_exists(
        env.cr, "printing_tray"
    ) and not openupgrade.table_exists(env.cr, "printing_tray_input"):
        openupgrade.rename_models(env.cr, [("printing.tray", "printing.tray.input")])
        openupgrade.rename_tables(env.cr, [("printing_tray", "printing_tray_input")])
        openupgrade.rename_fields(
            env,
            [
                (
                    "ir.actions.report",
                    "ir_actions_report",
                    "printer_tray_id",
                    "printer_input_tray_id",
                ),
                (
                    "printing.report.xml.action",
                    "printing_report_xml_action",
                    "printer_tray_id",
                    "printer_input_tray_id",
                ),
                (
                    "res.users",
                    "res_users",
                    "printer_tray_id",
                    "printer_input_tray_id",
                ),
            ],
        )
