from openupgradelib import openupgrade


def migrate(cr, version):
    openupgrade.rename_models(cr, [("printing.tray", "printing.tray.input")])
    openupgrade.rename_tables(cr, [("printing_tray", "printing_tray_input")])
    openupgrade.rename_fields(
        cr,
        [
            (
                "ir.actions.report",
                "ir_actions_report",
                "printer_tray_id",
                "printer_input_tray_id",
                None,
            ),
            (
                "printing.report.xml.action",
                "printing_report_xml_action",
                "printer_tray_id",
                "printer_input_tray_id",
                None,
            ),
            (
                "res.users",
                "res_users",
                "printer_tray_id",
                "printer_input_tray_id",
                None,
            ),
        ],
    )
