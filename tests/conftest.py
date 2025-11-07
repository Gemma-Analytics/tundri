import pytest
import os

from tundri.utils import get_snowflake_cursor


@pytest.fixture(scope="session")
def snowflake_cursor():
    cursor = get_snowflake_cursor()
    try:
        yield cursor
    finally:
        cursor.close()


@pytest.fixture(scope="session")
def test_credentials():
    return {
        "SNOWFLAKE_ACCOUNT": os.getenv("PERMISSION_BOT_ACCOUNT"),
        "SNOWFLAKE_USER": os.getenv("PERMISSION_BOT_USER"),
        "SNOWFLAKE_ROLE": os.getenv("PERMISSION_BOT_ROLE"),
        "SNOWFLAKE_DATABASE": os.getenv("PERMISSION_BOT_DATABASE"),
        "SNOWFLAKE_WAREHOUSE": os.getenv("PERMISSION_BOT_WAREHOUSE"),
    }


@pytest.fixture(scope="session")
def test_values():
    """
    Dict with values that integration tests use to create/drop/alter
    user/warehouses/databases
    """
    return {"test_user": "user1"}


@pytest.fixture(scope="session")
def users_to_skip():
    """
    List of users with admin priviliges, which cannot be inspected by the permifrost
    user and that should be skipped during drop, create, alter operations
    """
    return ["admin", "snowflake", "auto_dba"]
