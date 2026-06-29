from openupgradelib import openupgrade

# 18.0 shipped the label list view and its act_window.view link under "tree"
# xml ids. 19.0 renames both to "list" and adds the unique constraint
# act_window_view_unique_mode_per_action on (act_window_id, view_mode). The
# existing act_window.view row already holds "list" (converted on upgrade), so
# reloading the data under the new xml id would insert a duplicate list row and
# the constraint would abort the upgrade. Rename the xml ids up front so the
# reload updates the existing rows in place.
_XMLID_RENAMES = [
    (
        "printer_zpl2.act_open_printing_label_zpl2_view_tree",
        "printer_zpl2.act_open_printing_label_zpl2_view_list",
    ),
    (
        "printer_zpl2.view_printing_label_zpl2_tree",
        "printer_zpl2.view_printing_label_zpl2_list",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(env.cr, _XMLID_RENAMES)
