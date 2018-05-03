# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    cr.execute("""
        UPDATE ir_model_data SET module = 'label_zpl2'
        WHERE module = 'printer_zpl2'
        AND model = 'ir.model.fields'
        AND res_id IN (SELECT id
        FROM ir_model_fields
        WHERE model='printing.label.zpl2'
        AND name not in ('action_window_id','test_print_mode','printer_id'))

    """)

    cr.execute("""
        UPDATE ir_model_data SET module = 'label_zpl2'
        WHERE module = 'printer_zpl2'
        AND model = 'ir.model.fields'
        AND res_id IN (SELECT id
        FROM ir_model_fields
        WHERE model='printing.label.zpl2.component')
    """)
