from tundri.utils import plural, format_metadata_value, format_params


def test_plural():
    assert plural("user") == "users"
    assert plural("warehouse") == "warehouses"
    assert plural("database") == "databases"
    assert plural("schema") == "schemas"
    assert plural("role") == "roles"


def test_treat_metadata_value():
    assert format_metadata_value("dummy_key", "true") == True
    assert format_metadata_value("dummy_key", "false") == False
    assert format_metadata_value("dummy_key", "TRUE") == True
    assert format_metadata_value("dummy_key", "FALSE") == False
    assert format_metadata_value("dummy_key", "Something") == "something"
    assert format_metadata_value("rsa_public_key", "CaseSensitve") == "CaseSensitve"


def test_format_params():
    assert (
        format_params({"name": "test", "value": "test"})
        == "name = 'test', value = 'test'"
    )
    assert format_params({"name": 1, "value": 1}) == "name = 1, value = 1"
    assert format_params({"name": False, "value": True}) == "name = False, value = True"
    assert (
        format_params({"name": True, "value": "False"}) == "name = True, value = False"
    )
    # Special case for default_role, default_warehouse and default_namespace
    # that need to be formatted as uppercase
    assert (
        format_params({"default_role": "userrole_bob"})
        == "default_role = 'USERROLE_BOB'"
    )
    assert (
        format_params({"default_warehouse": "admin"}) == "default_warehouse = 'ADMIN'"
    )
    assert (
        format_params({"default_namespace": "dev_bob_raw"})
        == "default_namespace = 'DEV_BOB_RAW'"
    )
    assert (
        format_params({"default_namespace": "dev_bob_raw.github"})
        == "default_namespace = 'DEV_BOB_RAW.GITHUB'"
    )
