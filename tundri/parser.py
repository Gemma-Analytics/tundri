from yaml import load, Loader
from pprint import pprint
from typing import FrozenSet

from tundri.constants import OBJECT_TYPES, OBJECT_TYPE_MAP
from tundri.objects import SnowflakeObject, Schema, ConfigurationValueError
from tundri.utils import plural, format_metadata_value

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
            params = object_spec["meta"]  # Use all contents of meta as DDL parameters
            for name, value in params.items():
                params[name] = format_metadata_value(name, value)
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
