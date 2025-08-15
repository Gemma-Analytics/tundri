def test_connection(snowflake_cursor):
    """
    Tests whether connection to Snowflake was established succesfully
    """
    desired_output = 1
    test_query = f"SELECT {desired_output}"

    snowflake_cursor.execute(test_query)
    assert snowflake_cursor.fetchone()[0] == desired_output


def test_user_state(snowflake_cursor, test_credentials):
    """
    Tests user state after connecting to Snowflake
    """
    # The ROLE parameter is not explicitly specified when tundri establishes
    # the connection to Snowflake, so we are not checking its state
    test_values = [
        test_credentials["SNOWFLAKE_ACCOUNT"].upper(),
        test_credentials["SNOWFLAKE_USER"].upper(),
        test_credentials["SNOWFLAKE_DATABASE"].upper(),
        test_credentials["SNOWFLAKE_WAREHOUSE"].upper(),
    ]
    test_query = """
    SELECT 
        CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME(),
        CURRENT_USER(), 
        CURRENT_DATABASE(), 
        CURRENT_WAREHOUSE()
    """

    snowflake_cursor.execute(test_query)
    result = snowflake_cursor.fetchall()
    assert list(result[0]) == test_values
