from tundri.core import build_statements_list, build_summary_line, resolve_objects
from tundri.objects import User, Warehouse


def test_resolve_objects_generates_unset_for_removed_param():
    """Removing a param from spec should generate an UNSET statement."""
    existing = Warehouse(
        name="WH1",
        params={
            "warehouse_size": "xsmall",
            "auto_suspend": "60",
            "comment": "my warehouse",
        },  # noqa: E501
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
    """No UNSET: param value is 'null' (Snowflake default representation)."""
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
        },  # noqa: E501
    )
    ought = Warehouse(
        name="WH1",
        params={
            "warehouse_size": "medium",
            "auto_suspend": "60",
        },  # size changed, comment removed  # noqa: E501
    )

    result = resolve_objects(frozenset([existing]), frozenset([ought]))

    assert result["create"] == []
    assert result["drop"] == []
    assert len(result["alter"]) == 2
    stmts_combined = " ".join(result["alter"])
    assert " SET " in stmts_combined
    assert " UNSET " in stmts_combined


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


def test_build_summary_line_mixed_operations():
    """Summary line should show counts for each operation type."""
    statements = [
        "USE ROLE SYSADMIN",
        "DROP DATABASE old_db",
        "USE ROLE SYSADMIN",
        "CREATE WAREHOUSE wh1",
        "USE ROLE SYSADMIN",
        "CREATE DATABASE db1",
        "USE ROLE SECURITYADMIN",
        "ALTER USER foo SET rsa_public_key='...'",
        "USE ROLE SECURITYADMIN",
        "ALTER USER bar UNSET rsa_public_key",
    ]
    result = build_summary_line(statements)
    assert result == "2 CREATE, 2 ALTER (1 SET, 1 UNSET), 1 DROP"


def test_build_summary_line_no_statements():
    """Empty list should return None."""
    result = build_summary_line([])
    assert result is None


def test_build_summary_line_only_creates():
    """Only CREATE operations — ALTER and DROP should show 0."""
    statements = [
        "USE ROLE SYSADMIN",
        "CREATE WAREHOUSE wh1",
        "USE ROLE SYSADMIN",
        "CREATE DATABASE db1",
    ]
    result = build_summary_line(statements)
    assert result == "2 CREATE, 0 ALTER, 0 DROP"


def test_build_summary_line_only_alters_set():
    """Only ALTER SET — both sub-counts are shown even when UNSET count is 0."""
    statements = [
        "USE ROLE SECURITYADMIN",
        "ALTER USER foo SET rsa_public_key='...'",
    ]
    result = build_summary_line(statements)
    assert result == "0 CREATE, 1 ALTER (1 SET, 0 UNSET), 0 DROP"


def test_build_summary_line_only_alters_unset():
    """Only ALTER UNSET."""
    statements = [
        "USE ROLE SECURITYADMIN",
        "ALTER USER foo UNSET rsa_public_key",
    ]
    result = build_summary_line(statements)
    assert result == "0 CREATE, 1 ALTER (0 SET, 1 UNSET), 0 DROP"


# --- User UNSET behaviour ---


def test_resolve_objects_generates_unset_for_user_rsa_keys():
    """RSA key params generate UNSET when absent from spec (original behaviour)."""
    existing = User(
        name="alice",
        params={"default_role": "analyst", "rsa_public_key": "MIIBI..."},
    )
    ought = User(name="alice", params={"default_role": "analyst"})

    result = resolve_objects(frozenset([existing]), frozenset([ought]))

    assert result["create"] == []
    assert result["drop"] == []
    assert len(result["alter"]) == 1
    assert "UNSET" in result["alter"][0]
    assert "rsa_public_key" in result["alter"][0].lower()


def test_resolve_objects_generates_unset_for_expanded_user_params():
    """Newly added user params (email, display_name, etc.) also generate UNSET."""
    existing = User(
        name="bob",
        params={
            "default_role": "analyst",
            "email": "bob@example.com",
            "display_name": "Bob Smith",
            "comment": "managed user",
        },
    )
    ought = User(name="bob", params={"default_role": "analyst"})

    result = resolve_objects(frozenset([existing]), frozenset([ought]))

    assert result["create"] == []
    assert result["drop"] == []
    assert len(result["alter"]) == 1
    unset_stmt = result["alter"][0]
    assert "UNSET" in unset_stmt
    # All three absent params with non-empty Snowflake values should be unset
    assert "email" in unset_stmt.lower()
    assert "display_name" in unset_stmt.lower()
    assert "comment" in unset_stmt.lower()


def test_resolve_objects_no_unset_for_params_not_in_unset_list():
    """Params absent from spec but not in params_to_unset_if_absent are not UNSETed."""
    existing = User(
        name="carol",
        params={
            "default_role": "analyst",
            "type": "person",  # not in params_to_unset_if_absent
        },
    )
    ought = User(name="carol", params={"default_role": "analyst"})

    result = resolve_objects(frozenset([existing]), frozenset([ought]))

    assert result["alter"] == []


def test_resolve_objects_no_unset_for_user_param_already_empty_in_snowflake():
    """No UNSET when the param is already empty/null in Snowflake."""
    existing = User(
        name="dave",
        params={"default_role": "analyst", "email": "", "comment": "null"},
    )
    ought = User(name="dave", params={"default_role": "analyst"})

    result = resolve_objects(frozenset([existing]), frozenset([ought]))

    assert result["alter"] == []
