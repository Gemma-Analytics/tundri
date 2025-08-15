from pprint import pprint
from typing import FrozenSet

from tundri.constants import OBJECT_TYPES, OBJECT_TYPE_MAP, INSPECTOR_ROLE
from tundri.objects import SnowflakeObject, Schema
from tundri.utils import plural, get_snowflake_cursor, format_metadata_value

# Column names of SHOW statement are different than parameter names in DDL statements
parameter_name_map = {
    "warehouse": {
        "size": "warehouse_size",
        "type": "warehouse_type",
    },
}


def inspect_schemas() -> FrozenSet[Schema]:
    """Get schemas that exist based on Snowflake metadata.

    Returns:
        inspected_objects: set of instances of `SnowflakeObject` subclasses
    """
    # Keys are databases and values are list of schemas e.g. {'ANALYTICS': ['REPORTING']}
    existing_schemas = {}
    with get_snowflake_cursor() as cursor:
        cursor.execute(f"USE ROLE {INSPECTOR_ROLE}")
        cursor.execute("SHOW SCHEMAS IN ACCOUNT")
        schemas_list = [
            (row[4], row[1]) for row in cursor
        ]  # List of tuples: database, schema
    for database, schema in schemas_list:
        database = database.upper()
        schema = schema.upper()
        if not existing_schemas.get(database):
            existing_schemas[database] = []
        existing_schemas[database].append(schema)

    existing_schema_names = []
    for database, schemas in existing_schemas.items():
        for schema in schemas:
            existing_schema_names.append(f"{database}.{schema}")

    return frozenset([Schema(name=name) for name in existing_schema_names])


def inspect_object_type(object_type: str) -> FrozenSet[SnowflakeObject]:
    """Initialize Snowflake objects of a given type from Snowflake metadata.

    Args:
        object_type: Object type e.g. "database", "user", etc

    Returns:
        inspected_objects: set of instances of `SnowflakeObject` subclasses
    """
    if object_type == "schema":
        return inspect_schemas()

    with get_snowflake_cursor() as cursor:
        cursor.execute(f"USE ROLE {INSPECTOR_ROLE}")
        cursor.execute(f"SHOW {plural(object_type)}")
        desc = cursor.description
        column_names = [
            parameter_name_map.get(object_type, dict()).get(col[0], col[0]) for col in desc
        ]
        formatted_rows = [
            tuple(
                [
                    format_metadata_value(column_names[idx], value)
                    for idx, value in enumerate(row)
                ]
            )
            for row in cursor
        ]
    data = [dict(zip(column_names, row)) for row in formatted_rows]

    inspected_objects = []
    for object in data:
        name = object.pop("name")
        # Ignore Snowflake system objects
        if name.startswith("system$"):
            continue
        inspected_objects.append(OBJECT_TYPE_MAP[object_type](name=name, params=object))

    return frozenset(inspected_objects)


def run():
    inspected_objects = {plural(object_type): None for object_type in OBJECT_TYPES}

    inspected_objects["warehouses"] = inspect_object_type("warehouse")
    inspected_objects["databases"] = inspect_object_type("database")

    pprint(inspected_objects)


if __name__ == "__main__":
    run()
