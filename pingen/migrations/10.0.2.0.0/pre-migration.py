# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields

from openupgradelib.openupgrade import migrate as oumigrate, column_exists, table_exists, add_fields


@oumigrate(use_env=True)
def migrate(env, version):
    migrate_to_api_v2_field(
        env,
        "ir_attachment",
        "pingen_speed",
        "id",
        "pingen_document",
        "delivery_product",
        "attachment_id",
        "selection",
        "varchar",
        field_default="cheap",
        values_mapping={"1": "fast", "2": "cheap"},
    )
    migrate_to_api_v2_field(
        env,
        "ir_attachment",
        "pingen_color",
        "id",
        "pingen_document",
        "print_spectrum",
        "attachment_id",
        "selection",
        "varchar",
        field_default="grayscale",
        values_mapping={"0": "grayscale", "1": "color"},
    )

def migrate_to_api_v2_field(env, old_model_table, old_fname, old_model_id, new_model_table, new_fname, new_model_id, new_ftype, new_db_ftype, field_default=None, values_mapping=None):
    add_fields(env, [(new_fname, new_model_table.replace("_", "."), new_model_table, new_ftype, new_db_ftype, "pingen")])
    migrate_data(env.cr, old_model_table, old_fname, new_model_table, new_fname, old_model_id, new_model_id, values_mapping=values_mapping)

    
def create_column(cr, table_name, column_name, column_type, column_default=None):
    sql = """ALTER TABLE {table} ADD COLUMN {column} {type}};"""
    params = [table_name, column_name, column_type]
    if column_default:
        sql = sql.replace(";", "DEFAULT %s;" )
        params.append(column_default)
    cr.execute(sql, params)

def migrate_data(cr, old_table, old_fname, new_table, new_fname, old_table_key, new_table_key, values_mapping=None):
    sql = """
        UPDATE {table_to}
        SET {table_to_col} = {table_from_col}
        FROM {table_from}
        WHERE {table_to}.{table_to_id} = {table_from}.{table_from_id};"""
    format_params = {
        "table_to": new_table,
        "table_from": old_table,
        "table_to_col": new_fname,
        "table_from_col": old_fname,
        "table_to_id": new_table_key,
        "table_from_id": old_table_key
    }
    sql = sql.format(**format_params)
    cr.execute(sql)
    for old_val, new_val in values_mapping.items():
        values_sql = """
            UPDATE {table_to}
            SET {table_to_col} = {new_val}
            WHERE {table_to_col} = {old_val};
        """
        format_params.update({"old_val": old_val, "new_val": new_val})
        values_sql = values_sql.format(**format_params)
        cr.execute(sql)
