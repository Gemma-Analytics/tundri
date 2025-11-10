from tundri.core import build_statements_list, execute_ddl
from tundri.inspector import inspect_object_type


def test_user_creation(snowflake_cursor, test_credentials, test_values, users_to_skip):
    """
    Tests whether tundri succesfully creates a user in Snowflake
    """
    test_role = test_credentials["SNOWFLAKE_ROLE"]
    test_user = test_values["test_user"]
    test_statements = {
        "user": {
            "drop": [],
            "create": [f"USE ROLE {test_role}; CREATE USER {test_user}"],
            "alter": [],
        },
    }

    ddl_statements_seq = build_statements_list(test_statements, ["user"])
    execute_ddl(snowflake_cursor, ddl_statements_seq)
    assert test_user in [
        user.params["login_name"].lower()
        for user in inspect_object_type("user", users_to_skip)
    ]


def test_user_removal(snowflake_cursor, test_credentials, test_values, users_to_skip):
    """
    Tests whether tundri succesfully drops a user in Snowflake
    """
    test_role = test_credentials["SNOWFLAKE_ROLE"]
    test_user = test_values["test_user"]
    test_statements = {
        "user": {
            "drop": [f"USE ROLE {test_role}; DROP USER {test_user}"],
            "create": [],
            "alter": [],
        },
    }

    ddl_statements_seq = build_statements_list(test_statements, ["user"])
    execute_ddl(snowflake_cursor, ddl_statements_seq)
    assert test_user not in [
        user.params["login_name"].lower()
        for user in inspect_object_type("user", users_to_skip)
    ]
