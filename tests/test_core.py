from tundri.core import build_statements_list


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
