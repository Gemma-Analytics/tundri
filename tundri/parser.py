import secrets
import string

from yaml import load, Loader
from pprint import pprint
from typing import FrozenSet

from tundri.constants import OBJECT_TYPES, OBJECT_TYPE_MAP
from tundri.objects import SnowflakeObject, Schema, ConfigurationValueError
from tundri.utils import plural, format_metadata_value


def _generate_random_password(length: int = 32) -> str:
    """Generate a random password for Snowflake users that don't have one specified.

    Snowflake requires a password when creating a user via CREATE USER, even for
    service users that authenticate via RSA key pair. This generates a strong random
    password that satisfies Snowflake's password policy.
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Ensure at least one of each required character type
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(string.punctuation),
    ]
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    # Shuffle to avoid predictable positions
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    return "".join(password_list)

PERMIFROST_YAML_FILEPATH = "examples/permifrost.yml"


def parse_schemas(permifrost_spec: dict) -> FrozenSet[Schema]:
    """Get schemas that ought to exist based on specific role definitions.

    The way schemas are defined in Permifrost is different from the other objects. We
    need to infer which ones need to exist based on definitions of roles that should
    use/own them.

    Args:
        permifrost_spec: Dict with contents from Permifrost YAML file

    Returns:
        parsed_objects: set of instances of `Schema` class
    """
    # Keys are databases and values are list of schemas e.g. {'ANALYTICS': ['REPORTING']}
    ought_schemas = {}
    for role in permifrost_spec["roles"]:
        role_name, permi_defs = list(role.items())[0]
        if permi_defs.get("owns") and permi_defs["owns"].get("schemas"):
            for schema in permi_defs["owns"]["schemas"]:
                database, schema_name = schema.upper().split(".")
                if not schema_name == "*":
                    if not ought_schemas.get(database):
                        ought_schemas[database] = []
                    ought_schemas[database].append(schema_name)
        if permi_defs.get("privileges") and permi_defs["privileges"].get("schemas"):
            for schema in permi_defs["privileges"]["schemas"].get("read", []):
                database, schema_name = schema.upper().split(".")
                if not schema_name == "*":
                    if not ought_schemas.get(database):
                        ought_schemas[database] = []
                    if not schema_name in ought_schemas[database]:
                        ought_schemas[database].append(schema_name)
            for schema in permi_defs["privileges"]["schemas"].get("write", []):
                database, schema_name = schema.upper().split(".")
                if not schema_name == "*":
                    if not ought_schemas.get(database):
                        ought_schemas[database] = []
                    if not schema_name in ought_schemas[database]:
                        ought_schemas[database].append(schema_name)

    ought_schema_names = []
    for database, schemas in ought_schemas.items():
        for schema in schemas:
            ought_schema_names.append(f"{database}.{schema}")

    return frozenset([Schema(name=name) for name in ought_schema_names])


def parse_object_type(
    permifrost_spec: dict, object_type: str
) -> FrozenSet[SnowflakeObject]:
    """Initialize Snowflake objects of a given type from Permifrost spec.

    Args:
        permifrost_spec: Dict with contents from Permifrost YAML file
        object_type: Object type e.g. "database", "user", etc

    Returns:
        parsed_objects: set of instances of `SnowflakeObject` subclasses
    """
    if object_type == "schema":
        return parse_schemas(permifrost_spec)

    parsed_objects = []
    for object in permifrost_spec.get(plural(object_type), []):
        # Each object is a dict with a single key (its name) and a dict containing the spec as value
        object_name = list(object.keys())[0]
        object_spec = object[object_name]
        params = dict()
        if "meta" in object_spec.keys():
            params = dict(object_spec["meta"])  # Copy to avoid mutating the input
            for name, value in params.items():
                params[name] = format_metadata_value(name, value)
        # Snowflake requires a password in CREATE USER statements. If none is
        # specified in the YAML (common for service users with key-pair auth),
        # generate a random one so the DDL succeeds. The password is never
        # usable in practice — especially for can_login: no users.
        if object_type == "user" and "password" not in params:
            params["password"] = _generate_random_password()
            params["must_change_password"] = True
        new_parsed_object = OBJECT_TYPE_MAP[object_type](
            name=object_name, params=params
        )
        if not new_parsed_object.check_required_params():
            raise ConfigurationValueError(
                f"Required parameters for object '{object_name}' of type '{object_type}' missing: {new_parsed_object.get_missing_required_params()}"
            )
        parsed_objects.append(new_parsed_object)

    return frozenset(parsed_objects)


def run():
    permifrost_spec = load(open(PERMIFROST_YAML_FILEPATH, "r"), Loader=Loader)

    parsed_objects = {plural(object_type): None for object_type in OBJECT_TYPES}

    parsed_objects["warehouses"] = parse_object_type(permifrost_spec, "warehouse")
    parsed_objects["databases"] = parse_object_type(permifrost_spec, "database")
    parsed_objects["roles"] = parse_object_type(permifrost_spec, "role")
    parsed_objects["users"] = parse_object_type(permifrost_spec, "user")
    parsed_objects["schemas"] = parse_object_type(permifrost_spec, "schema")

    pprint(parsed_objects)


if __name__ == "__main__":
    run()
