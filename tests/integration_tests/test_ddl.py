from tundri.core import build_statements_list, execute_ddl
from tundri.inspector import inspect_object_type


def test_user_creation(test_credentials, test_values, users_to_skip):
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
    execute_ddl(ddl_statements_seq)
    assert test_user in [
        user.params["login_name"].lower()
        for user in inspect_object_type("user", users_to_skip)
    ]


def test_user_unset_param(test_credentials, test_values, users_to_skip):
    """
    Tests that tundri successfully executes UNSET statements to clear a user
    attribute that existed in Snowflake but was removed from the spec.

    This simulates the scenario where a param (e.g. comment) is removed from the
    Permifrost spec: tundri should generate and execute ALTER ... UNSET to reset it
    to the Snowflake default.
    """
    test_role = test_credentials["SNOWFLAKE_ROLE"]
    test_user = test_values["test_user"]
    test_comment = "integration_test_comment"

    # Step 1: Set a comment on the existing test user to simulate a param in Snowflake
    set_statements = {
        "user": {
            "drop": [],
            "create": [],
            "alter": [
                f"USE ROLE {test_role}; ALTER USER {test_user} SET comment='{test_comment}'"
            ],
        },
    }
    execute_ddl(build_statements_list(set_statements, ["user"]))

    # Verify the comment was set
    users_after_set = inspect_object_type("user", users_to_skip)
    user_after_set = next(
        u for u in users_after_set if u.name.lower() == test_user.lower()
    )
    assert user_after_set.params.get("comment") == test_comment

    # Step 2: Execute an UNSET statement to remove the comment
    # (simulating the param being removed from the spec)
    unset_statements = {
        "user": {
            "drop": [],
            "create": [],
            "alter": [
                f"USE ROLE {test_role}; ALTER USER {test_user} UNSET comment"
            ],
        },
    }
    execute_ddl(build_statements_list(unset_statements, ["user"]))

    # Verify the comment was cleared
    users_after_unset = inspect_object_type("user", users_to_skip)
    user_after_unset = next(
        u for u in users_after_unset if u.name.lower() == test_user.lower()
    )
    # Snowflake returns the string 'null' for cleared/default fields (not Python None)
    assert user_after_unset.params.get("comment") in (None, "null", "")


def test_user_removal(test_credentials, test_values, users_to_skip):
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
    execute_ddl(ddl_statements_seq)
    assert test_user not in [
        user.params["login_name"].lower()
        for user in inspect_object_type("user", users_to_skip)
    ]
