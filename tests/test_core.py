from tundri.core import build_statements_list, resolve_objects
from tundri.objects import User, Warehouse


def test_resolve_objects_generates_unset_for_removed_param():
    """Removing a param from spec should generate an UNSET statement."""
    existing = Warehouse(
        name="WH1",
        params={
            "warehouse_size": "xsmall",
            "auto_suspend": "60",
            "comment": "my warehouse",
        },
    )
    ought = Warehouse(
        name="WH1",
        params={"warehouse_size": "xsmall", "auto_suspend": "60"},  # comment removed
    )

    result = resolve_objects(frozenset([existing]), frozenset([ought]))

    assert result["create"] == []
    assert result["drop"] == []
    assert len(result["alter"]) == 1
    unset_stmt = result["alter"][0]
    assert "UNSET" in unset_stmt
    assert "comment" in unset_stmt.lower()


def test_resolve_objects_no_unset_when_param_not_set_in_snowflake():
    """No UNSET should be generated when the param has no value in Snowflake."""
    existing = Warehouse(
        name="WH1",
        params={"warehouse_size": "xsmall", "auto_suspend": "60", "comment": ""},
    )
    ought = Warehouse(
        name="WH1",
        params={"warehouse_size": "xsmall", "auto_suspend": "60"},
    )

    result = resolve_objects(frozenset([existing]), frozenset([ought]))

    assert result["alter"] == []


def test_resolve_objects_no_unset_when_param_is_null_string_in_snowflake():
    """No UNSET when the param value is 'null' (Snowflake default representation)."""
    existing = Warehouse(
        name="WH1",
        params={"warehouse_size": "xsmall", "auto_suspend": "60", "comment": "null"},
    )
    ought = Warehouse(
        name="WH1",
        params={"warehouse_size": "xsmall", "auto_suspend": "60"},
    )

    result = resolve_objects(frozenset([existing]), frozenset([ought]))

    assert result["alter"] == []


def test_resolve_objects_generates_set_and_unset_simultaneously():
    """Both SET and UNSET can be generated in the same run for the same object."""
    existing = Warehouse(
        name="WH1",
        params={
            "warehouse_size": "xsmall",
            "auto_suspend": "60",
            "comment": "old comment",
        },
    )
    ought = Warehouse(
        name="WH1",
        params={
            "warehouse_size": "medium",
            "auto_suspend": "60",
        },  # size changed, comment removed
    )

    result = resolve_objects(frozenset([existing]), frozenset([ought]))

    assert result["create"] == []
    assert result["drop"] == []
    assert len(result["alter"]) == 2
    stmts_combined = " ".join(result["alter"])
    assert " SET " in stmts_combined
    assert " UNSET " in stmts_combined


def test_resolve_objects_no_unset_for_non_rsa_user_params():
    """Non-RSA user params (disabled, login_name, comment, etc.) never UNSET."""
    existing = User(
        name="testuser",
        params={
            "default_role": "testrole",
            "disabled": "false",
            "login_name": "testuser",
            "comment": "some comment",
            "email": "test@example.com",
        },
    )
    ought = User(
        name="testuser",
        params={"default_role": "testrole"},
    )

    result = resolve_objects(frozenset([existing]), frozenset([ought]))

    unset_stmts = [s for s in result["alter"] if "UNSET" in s]
    assert unset_stmts == [], f"Unexpected UNSET statements: {unset_stmts}"


def test_resolve_objects_generates_unset_for_rsa_keys():
    """RSA public keys should still generate UNSET when removed from spec."""
    existing = User(
        name="testuser",
        params={
            "default_role": "testrole",
            "rsa_public_key": "MIIBIjANBgkq...",
        },
    )
    ought = User(
        name="testuser",
        params={"default_role": "testrole"},
    )

    result = resolve_objects(frozenset([existing]), frozenset([ought]))

    unset_stmts = [s for s in result["alter"] if "UNSET" in s]
    assert len(unset_stmts) == 1
    assert "rsa_public_key" in unset_stmts[0].lower()


def test_build_statements_list():
    # Prepare test input
    test_statements = {
        "user": {
            "drop": [
                "USE ROLE admin; DROP USER user1",
                "USE ROLE admin; DROP USER user2",
            ],
            "create": [
                "USE ROLE admin; CREATE USER user1",
                "USE ROLE admin; CREATE USER user2",
            ],
            "alter": ["USE ROLE admin; ALTER USER user1 SET password='newpass'"],
        },
        "warehouse": {
            "drop": [],
            "create": ["USE ROLE admin; CREATE WAREHOUSE wh1"],
            "alter": ["USE ROLE admin; ALTER WAREHOUSE wh1 SET auto_suspend = 60"],
        },
    }

    # Call the function
    result = build_statements_list(test_statements, ["user", "warehouse"])

    # Assert the expected output
    expected_output = [
        "USE ROLE admin",
        "DROP USER user1",
        "USE ROLE admin",
        "DROP USER user2",
        "USE ROLE admin",
        "CREATE USER user1",
        "USE ROLE admin",
        "CREATE USER user2",
        "USE ROLE admin",
        "ALTER USER user1 SET password='newpass'",
        "USE ROLE admin",
        "CREATE WAREHOUSE wh1",
        "USE ROLE admin",
        "ALTER WAREHOUSE wh1 SET auto_suspend = 60",
    ]

    assert result == expected_output
