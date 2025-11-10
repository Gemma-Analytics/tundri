import logging
import os
from typing import FrozenSet, Dict, List

from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Prompt
from yaml import load, Loader

from tundri.constants import (
    OBJECT_TYPES,
    OBJECT_ROLE_MAP,
    SYSTEM_DEFINED_ROLES,
)
from tundri.inspector import inspect_object_type
from tundri.objects import SnowflakeObject
from tundri.parser import parse_object_type
from tundri.utils import (
    get_configs,
    get_snowflake_cursor,
    format_params,
    get_existing_user,
)


all_ddl_statements = {object_type: None for object_type in OBJECT_TYPES}

drop_template = "USE ROLE {role};DROP {object_type} {name};"
create_template = "USE ROLE {role};CREATE {object_type} {name} {extra_sql};"
alter_template = "USE ROLE {role};ALTER {object_type} {name} SET {parameters};"

objects_to_ignore_in_alter = {"user": ["snowflake"]}
params_to_ignore_in_alter = {
    "user": ["password", "must_change_password"],
    "warehouse": ["initially_suspended", "statement_timeout_in_seconds"],
}


logging.basicConfig(
    level="WARN", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)
log.setLevel("INFO")
console = Console()

# Compatible with GitHub, GitLab and Bitbucket
IS_CI_RUN = os.getenv("CI") == "true"


def build_statements_list(
    statements: Dict, object_types: List[str] = OBJECT_TYPES
) -> List:
    """
    Build a list of statements to be executed from a dictionary of statements with the
    structure:
    {
        "user": {
            "drop": ["DROP USER ...", "DROP USER ..."],
            "create": ["CREATE USER ..., "CREATE USER ..."],
            "alter": ["ALTER USER ..., "ALTER USER ..."],
        }
    }

    To a list of statements like:
    ["DROP USER ...", "DROP USER ...", "CREATE USER ..., "ALTER USER ..."]

    Args:
        statements: dict with the list of statements of each type (e.g. create, drop)
                    it assumes statements come as pairs  like "USE ROLE...; CREATE/DROP ..."
        object_types: list of object types to process, defaults to OBJECT_TYPES constant

    Returns:
        statements_seq: list with drop, create and alter statements in sequence for all
                        object types
    """
    statements_seq = []
    for object_type in object_types:
        for operation in ["drop", "create", "alter"]:  # Order matters
            for statement_pair in statements[object_type][operation]:
                for s in statement_pair.split(";"):
                    if s:  # Ignore empty strings
                        statements_seq.append(s.strip())
    return statements_seq


def print_ddl_statements(statements: Dict) -> None:
    """Print DDL statements to be executed."""
    if not statements:
        console.log(
            "No statements to execute (the state of Snowflake objects matches the Permifrost spec)\n"
        )
        return
    for s in statements:
        if s.startswith("USE ROLE"):
            continue
        console.log(f"[italic]- {s}[/italic]")
    console.log()


def execute_ddl(statements: List) -> None:
    """Execute drop, create and alter statements in sequence for each object type.

    Args:
        statements: list with drop, create and alter statements in sequence for all
                    object types
    """
    console.log("\n[bold]Executing DDL statements[/bold]:")
    with get_snowflake_cursor() as cursor:
        for s in statements:
            cursor.execute(s)
            if s.startswith("USE ROLE"):
                continue
            console.log(f"[green]\u2713[/green] [italic]{s}[/italic]")


def ignore_system_defined_roles(
    objects: FrozenSet[SnowflakeObject],
) -> FrozenSet[SnowflakeObject]:
    """Ignore system-defined roles to avoid errors when trying to create or drop them."""
    return frozenset(
        [
            obj
            for obj in objects
            if not (obj.type == "role" and obj.name in SYSTEM_DEFINED_ROLES)
        ]
    )


def ignore_existing_users(
    objects: FrozenSet[SnowflakeObject],
) -> FrozenSet[SnowflakeObject]:
    """
    Ignore users that already exist

    Args:
        cursor: Active Snowflake cursor
        ought_objects: User objects to check

    Returns:
        "objects" parameter, but pruned of existing users
    """
    with get_snowflake_cursor() as cursor:
        users_list = get_existing_user(cursor)  # List of users (Strings)
        return frozenset([obj for obj in objects if obj.name.lower() not in users_list])


def resolve_objects(
    existing_objects: FrozenSet[SnowflakeObject],
    ought_objects: FrozenSet[SnowflakeObject],
) -> Dict:
    """Prepare DROP, CREATE and ALTER statements for an object type.

    Args:
        existing_objects: Set of Snowflake objects that currently exist
        ought_objects: Set of Snowflake objects that are expected to exist

    Returns:
        ddl_statements: dict with drop, create and alter keys with lists of DDL statments
                        to be executed for the given object type
    """
    ddl_statements = {
        "drop": [],
        "create": [],
        "alter": [],
    }

    # Infer type from arguments
    object_type = list(existing_objects)[0].type
    console.log(f"Resolving {object_type} objects")

    role = OBJECT_ROLE_MAP[object_type]

    # Check which objects to drop/create/keep
    objects_to_drop = existing_objects.difference(ought_objects)
    if object_type == "schema":  # Schemas should not be dropped
        objects_to_drop = frozenset()
    objects_to_create = ought_objects.difference(existing_objects)
    objects_to_keep = ought_objects.intersection(existing_objects)

    # Remove create or drop statements for system-defined roles
    objects_to_create = ignore_system_defined_roles(objects_to_create)
    objects_to_drop = ignore_system_defined_roles(objects_to_drop)
    if object_type == "user":
        # Since we are skipping some users with admin priviliges during object inspection,
        # tundri won't know whether those users already exist, and will try to create them
        # even if they already exist. Adding a IF NOT EXIST flag to the CREATE command
        # will only work partially, because tundri still would issue prompts for the
        # affected users
        objects_to_create = ignore_existing_users(objects_to_create)

    # Prepare CREATE/DROP statements
    ddl_statements["create"] = [
        create_template.format(
            role=role,
            object_type=object_type,
            name=obj.name,
            extra_sql=format_params(obj.params),
        ).strip()
        for obj in objects_to_create
    ]
    ddl_statements["drop"] = [
        drop_template.format(role=role, object_type=object_type, name=obj.name)
        for obj in objects_to_drop
    ]

    # Prepare ALTER statements
    existing_objects_to_keep = sorted(
        [obj for obj in existing_objects if obj in objects_to_keep]
    )
    ought_objects_to_keep = sorted(
        [obj for obj in ought_objects if obj in objects_to_keep]
    )

    for existing, ought in zip(existing_objects_to_keep, ought_objects_to_keep):
        assert (
            existing == ought
        )  # Leverages custom __eq__ implementation to compare name and type
        if not ought.params:
            continue
        if existing.params == ought.params:
            continue

        for p in params_to_ignore_in_alter.get(object_type, list()):
            ought.params.pop(p, None)

        ought_params_set = set(ought.params.items())
        existing_params_set = set(existing.params.items())
        params_to_alter_set = ought_params_set.difference(existing_params_set)
        if not params_to_alter_set:
            continue
        if ought.name in objects_to_ignore_in_alter.get(object_type, list()):
            continue
        ddl_statements["alter"].append(
            alter_template.format(
                role=role,
                object_type=object_type,
                name=ought.name,
                parameters=format_params(dict(params_to_alter_set)),
            )
        )

    return ddl_statements


def drop_create_objects(
    permifrost_spec_path: str, is_dry_run: bool, users_to_skip: List[str]
):
    """
    Drop and create Snowflake objects based on Permifrost specification and inspection of Snowflake metadata.

    Args:
        permifrost_spec_path: path to the Permifrost specification file
        is_dry_run: flag to run the operation in dry-run mode
        users_to_skip: list of users to skip during rom drop, create, alter operations

    Returns:
        bool: True if the operation was successful, False otherwise
    """
    permifrost_spec = load(open(permifrost_spec_path, "r"), Loader=Loader)

    for object_type in OBJECT_TYPES:
        existing_objects = inspect_object_type(object_type, users_to_skip)
        ought_objects = parse_object_type(permifrost_spec, object_type)
        all_ddl_statements[object_type] = resolve_objects(
            existing_objects,
            ought_objects,
        )

    console.log("\n[bold]DDL statements to be executed[/bold]:")
    ddl_statements_seq = build_statements_list(all_ddl_statements)
    print_ddl_statements(ddl_statements_seq)
    drop_statements = [s for s in ddl_statements_seq if s.startswith("DROP")]

    if IS_CI_RUN:
        console.log(
            "[bold][yellow]CI run detected[/bold][/yellow]: Skipping manual confirmations"
        )

    if not is_dry_run and not IS_CI_RUN:
        configs = get_configs()
        console.log(
            f"\n[bold][blue]INFO[/bold][/blue]: Executing for Snowflake account: {configs['account']}"
        )
        user_input = Prompt.ask(
            f"\n\t>>> Type [bold]{configs['account']}[/bold] to proceed or any other key to abort"
        )
        if user_input.lower() != configs["account"].lower():
            console.log()
            console.log("Exited without executing any statements")
            return False

    if not is_dry_run and not IS_CI_RUN and drop_statements:
        console.log(
            f"\n[bold][red]WARNING[/bold][/red]: The following DROP statements are about to be executed: {(drop_statements)}"
        )
        user_input = Prompt.ask(
            "\n\t>>> Type [bold]drop[/bold] to proceed or any other key to abort"
        )
        if user_input.lower() != "drop":
            console.log()
            console.log("Exited without executing any statements")
            return False

    if not is_dry_run:
        execute_ddl(ddl_statements_seq)

    return True
