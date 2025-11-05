import logging
from pprint import pprint
from typing import FrozenSet, List

from rich.console import Console
from rich.logging import RichHandler

from tundri.constants import OBJECT_TYPES, OBJECT_TYPE_MAP, INSPECTOR_ROLE
from tundri.objects import SnowflakeObject, Schema, User
from tundri.utils import (
    plural,
    get_snowflake_cursor,
    format_metadata_value,
    get_existing_user,
)

from snowflake.connector.errors import ProgrammingError

# Column names of SHOW statement are different than parameter names in DDL statements
parameter_name_map = {
    "warehouse": {
        "size": "warehouse_size",
        "type": "warehouse_type",
    },
}


logging.basicConfig(
    level="WARN", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)
log.setLevel("INFO")
console = Console()


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


def inspect_users(skip_user: List[str]) -> FrozenSet[User]:
    """
    Get metadata of USER objects, using Snowflake's DESCRIBE command.

    Note:
    We are using Snowflake's SHOW instead of it's DESCRIBE command to inspect
    objects. For most objects (Databases, Schemas, Warehouses), SHOW allows us to
    fetch object metadata, while DESCRIBE would only the structure/schema of
    a single object.

    The only exception to this are USER objects: those objects have no internal
    structure, and their metadata essentially describes their structure. Thus,
    SHOW and DESCRIBE return similar information, with DESCRIBE returning a more
    complete set of metadata of a user. The following attributes are missing from
    DESCRIBE and need to be added manually if required:
    [created_on, owner, last_success_login, expires_at_time, locked_until_time,
    has_password, has_rsa_public_key]

    Returns:
        data: Immutable set of user objects
    """
    data = []
    with get_snowflake_cursor() as cursor:
        users_list = get_existing_user(cursor)  # List of users (Strings)
        for user in users_list:
            try:
                cursor.execute(f"USE ROLE {INSPECTOR_ROLE}")
                cursor.execute(f"DESCRIBE USER {user}")

                # DESCRIBE returns one row per user attribute, while SHOW returns one column
                # per user attribute. Pivot the result of DESCRIBE so it works with the
                # `format_metadata_value()` function
                attributes = {
                    row[0]: row[1] for row in cursor
                }  # Dict of user attributes in the form "attribute: value"
                formatted_row = {
                    key.lower(): format_metadata_value(key.lower(), value)
                    for _, (key, value) in enumerate(attributes.items())
                }  # `format_metadata_value()` expects keys to be lowercase
                name = formatted_row.pop("name")
                data.append(User(name=name, params=formatted_row))
            except ProgrammingError as e:
                if "insufficient privileges" in e.msg.lower() and user in skip_user:
                    console.log(
                        "[bold][red]WARNING[/bold][/red]: Skipping metadata retrieval",
                        f"for user {user}: Permifrost user doesn't have DESCRIBE",
                        "privileges on this object",
                    )
                else:
                    raise e
    return frozenset(data)


def inspect_object_type(
    object_type: str, skip_user: List[str]
) -> FrozenSet[SnowflakeObject]:
    """Initialize Snowflake objects of a given type from Snowflake metadata.

    Args:
        object_type: Object type e.g. "database", "user", etc
        skip_user: list of users to skip during inspection

    Returns:
        inspected_objects: set of instances of `SnowflakeObject` subclasses
    """
    if object_type == "schema":
        return inspect_schemas()
    if object_type == "user":
        return inspect_users(skip_user)

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
