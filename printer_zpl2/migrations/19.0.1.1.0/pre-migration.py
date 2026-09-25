# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    """The Labelary mode is shared by all the labels, in a configuration
    parameter: enable it if it was enabled on any label"""
    cr.execute("SELECT 1 FROM printing_label_zpl2 WHERE test_labelary_mode LIMIT 1")
    if cr.fetchone():
        cr.execute(
            """
            INSERT INTO ir_config_parameter
                (key, value, create_uid, create_date, write_uid, write_date)
            VALUES
                ('printer_zpl2.test_labelary_mode', 'True', 1, now(), 1, now())
            ON CONFLICT (key) DO UPDATE SET value = 'True', write_date = now()
            """
        )
    cr.execute("ALTER TABLE printing_label_zpl2 DROP COLUMN test_labelary_mode")
