import os

from tundri.objects import (
    Warehouse,
    Database,
    User,
    Role,
    Schema,
)


ENV_VAR_OVERRIDE_ROLE = "TUNDRI_DROP_CREATE_ROLE"

OBJECT_TYPE_MAP = {
    "warehouse": Warehouse,
    "database": Database,
    "user": User,
    "role": Role,
    "schema": Schema,
}

OBJECT_TYPES = list(OBJECT_TYPE_MAP.keys())

# For backwards compatibility, we allow setting the role via environment variables
# so previous setups that used `permifrost` role will continue to work
OBJECT_ROLE_MAP = {
    "warehouse": os.getenv(ENV_VAR_OVERRIDE_ROLE, "SYSADMIN"),
    "database": os.getenv(ENV_VAR_OVERRIDE_ROLE, "SYSADMIN"),
    "schema": os.getenv(ENV_VAR_OVERRIDE_ROLE, "SYSADMIN"),
    "user": os.getenv(ENV_VAR_OVERRIDE_ROLE, "SECURITYADMIN"),
    "role": os.getenv(ENV_VAR_OVERRIDE_ROLE, "SECURITYADMIN"),
}
# SYSADMIN can't see objects after ownership is transferred,
# so we need to alwaysuse SECURITYADMIN for inspection
INSPECTOR_ROLE = os.getenv(ENV_VAR_OVERRIDE_ROLE, "SECURITYADMIN")

SYSTEM_DEFINED_ROLES = [
    "accountadmin",
    "securityadmin",
    "sysadmin",
    "useradmin",
    "orgadmin",
]

STRING_CASING_CONVERSION_MAP = {
    "rsa_public_key": str,  # Keep case
}
