# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from collections import namedtuple

from openupgradelib.openupgrade import (
    add_fields,
    column_exists,
    logged_query,
    migrate as oumigrate,
    table_exists,
)
from psycopg2 import sql

field_definition = namedtuple("FieldDefinition", ["name", "type", "db_type"])


@oumigrate(use_env=True)
def migrate(env, version):
    move_and_migrate_to_api_v2_field(
        env,
        "ir_attachment",
        field_definition("pingen_speed", "selection", "integer"),
        "id",
        "pingen_document",
        field_definition("delivery_product", "selection", "varchar"),
        "attachment_id",
        field_default="cheap",
        values_mapping={"1": "fast", "2": "cheap"},
    )
    move_and_migrate_to_api_v2_field(
        env,
        "ir_attachment",
        field_definition("pingen_color", "selection", "integer"),
        "id",
        "pingen_document",
        field_definition("print_spectrum", "selection", "varchar"),
        "attachment_id",
        field_default="grayscale",
        values_mapping={"0": "grayscale", "1": "color"},
    )
    move_and_migrate_to_api_v2_field(
        env,
        "ir_attachment",
        field_definition("pingen_send", "boolean", "bool"),
        "id",
        "pingen_document",
        field_definition("auto_send", "boolean", "bool"),
        "attachment_id",
        field_default="True",
    )
    migrate_to_api_v2_field(
        env,
        "pingen_document",
        field_definition("pingen_id", "integer", "int4"),
        field_definition("pingen_uuid", "char", "varchar"),
    )
    migrate_to_api_v2_field(
        env,
        "pingen_document",
        field_definition("post_status", "char", "varchar"),
        field_definition("pingen_status", "char", "varchar"),
    )


def migrate_to_api_v2_field(
    env, table_name, old_field_definition, new_field_definition
):
    if table_exists(env.cr, table_name) and not column_exists(
        env.cr, table_name, new_field_definition.name
    ):
        add_fields(
            env,
            [
                (
                    new_field_definition.name,
                    table_name.replace("_", "."),
                    table_name,
                    new_field_definition.type,
                    new_field_definition.db_type,
                    "pingen",
                )
            ],
        )
        migrate_data(env.cr, table_name, old_field_definition, new_field_definition)


def move_and_migrate_to_api_v2_field(
    env,
    old_model_table,
    old_field_definition,
    old_model_id,
    new_model_table,
    new_field_definition,
    new_model_id,
    field_default=None,
    values_mapping={},
):
    if table_exists(env.cr, new_model_table) and not column_exists(
        env.cr, new_model_table, new_field_definition.name
    ):
        add_fields(
            env,
            [
                (
                    new_field_definition.name,
                    new_model_table.replace("_", "."),
                    new_model_table,
                    new_field_definition.type,
                    new_field_definition.db_type,
                    "pingen",
                )
            ],
        )
        move_and_migrate_data(
            env.cr,
            old_model_table,
            old_field_definition,
            new_model_table,
            new_field_definition,
            old_model_id,
            new_model_id,
            values_mapping=values_mapping,
        )


def migrate_data(cr, table_name, old_field_definition, new_field_definition):
    query = sql.SQL(
        """
        UPDATE {table_name}
        SET {new_fname} = {old_fname};
    """
    )
    format_params = {
        "table_name": sql.Identifier(table_name),
        "new_fname": sql.Identifier(new_field_definition.name),
        "old_fname": sql.Identifier(old_field_definition.name),
    }
    if old_field_definition.db_type != new_field_definition.db_type:
        format_params.update(
            {
                "old_fname": sql.SQL(
                    "%s::%s" % (old_field_definition.name, new_field_definition.db_type)
                )
            }
        )
    query = query.format(**format_params)
    logged_query(cr, query)


def move_and_migrate_data(
    cr,
    old_table,
    old_field_definition,
    new_table,
    new_field_definition,
    old_table_key,
    new_table_key,
    values_mapping={},
):
    query = sql.SQL(
        """
        UPDATE {table_to}
        SET {table_to_col} = {table_from_col}
        FROM {table_from}
        WHERE {table_to}.{table_to_id} = {table_from}.{table_from_id};"""
    )
    format_params = {
        "table_to": sql.Identifier(new_table),
        "table_from": sql.Identifier(old_table),
        "table_to_col": sql.Identifier(new_field_definition.name),
        "table_from_col": sql.Identifier(old_field_definition.name),
        "table_to_id": sql.Identifier(new_table_key),
        "table_from_id": sql.Identifier(old_table_key),
    }
    query = query.format(**format_params)
    logged_query(cr, query)
    for old_val, new_val in values_mapping.items():
        values_query = sql.SQL(
            """
            UPDATE {table_to}
            SET {table_to_col} = {new_val}
            WHERE {table_to_col} = {old_val};
        """
        )
        if new_val.isdigit():
            format_params["new_val"] = sql.SQL(new_val)
        else:
            format_params["new_val"] = sql.Literal(new_val)
        format_params.update({"old_val": sql.SQL(old_val)})
        if old_field_definition.db_type != new_field_definition.db_type:
            format_params.update(
                {"old_val": sql.SQL("%s::%s" % (old_val, new_field_definition.db_type))}
            )
        values_query = values_query.format(**format_params)
        logged_query(cr, values_query)
