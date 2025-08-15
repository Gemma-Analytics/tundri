import pytest
from yaml import load, Loader

from tundri.parser import parse_object_type
from tundri.objects import ConfigurationValueError


def test_user_basic_attributes():
    """Asserts that basic user attributes are correctly parsed from the spec"""
    spec_path = "tests/data/correct_required_params_spec.yml"
    permifrost_spec = load(open(spec_path, "r"), Loader=Loader)

    users = parse_object_type(permifrost_spec, "user")

    # Get the first (and only) user
    user = next(iter(users))

    # Verify basic user attributes are parsed correctly
    assert user.name == "bob"
    assert user.params["default_role"] == "userrole_bob"
    assert user.params["default_warehouse"] == "develop"
    assert "can_login" in permifrost_spec["users"][0]["bob"]
    assert permifrost_spec["users"][0]["bob"]["can_login"] == True
    assert "member_of" in permifrost_spec["users"][0]["bob"]
    assert "userrole_bob" in permifrost_spec["users"][0]["bob"]["member_of"]


def test_required_params_user():
    """Asserts that parser object initialization checks for required parameters correctly for users"""
    correct_user_spec_path = "tests/data/correct_required_params_spec.yml"
    correct_permifrost_spec = load(open(correct_user_spec_path, "r"), Loader=Loader)
    parse_object_type(correct_permifrost_spec, "user")

    incorrect_user_spec_path = "tests/data/incorrect_required_params_spec.yml"
    incorrect_permifrost_spec = load(open(incorrect_user_spec_path, "r"), Loader=Loader)
    with pytest.raises(ConfigurationValueError) as exc:
        parse_object_type(incorrect_permifrost_spec, "user")
    assert "missing: ['default_role']" in str(exc.value)


def test_required_params_warehouse():
    """Asserts that parser object initialization checks for required parameters correctly for warehouses"""
    correct_warehouse_spec_path = "tests/data/correct_required_params_spec.yml"
    correct_permifrost_spec = load(
        open(correct_warehouse_spec_path, "r"), Loader=Loader
    )
    parse_object_type(correct_permifrost_spec, "warehouse")

    incorrect_warehouse_spec_path = "tests/data/incorrect_required_params_spec.yml"
    incorrect_permifrost_spec = load(
        open(incorrect_warehouse_spec_path, "r"), Loader=Loader
    )
    with pytest.raises(ConfigurationValueError) as exc:
        parse_object_type(incorrect_permifrost_spec, "warehouse")
    assert "missing: ['warehouse_size', 'auto_suspend']" in str(exc.value)


def test_meta_params_case_conversion():
    """Asserts that meta parameters are converted to lowercase when parsed"""
    uppercase_spec_path = "tests/data/uppercase_meta_params_spec.yml"
    permifrost_spec = load(open(uppercase_spec_path, "r"), Loader=Loader)

    # Parse the user with uppercase meta parameters
    users = parse_object_type(permifrost_spec, "user")

    # Get the first (and only) user
    user = next(iter(users))

    # Verify meta parameter values are correct
    assert user.params["default_role"] == "userrole_test"
    assert user.params["default_warehouse"] == "test_warehouse"
    assert user.params["password"] == "1passwordvault"
    assert user.params["must_change_password"] == True
    assert (
        user.params["rsa_public_key"] == "-----BEGIN PUBLIC KEY-----\n"
        "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAorPOOOdYipGVCUWbV1Fj\n"
        "Aw4+2LM9ePVk/yX8sIqrbhzE/6X4Q3W65C2xkB+UA9WfqoqVTIwvran9ElQj05sk\n"
        "Ev8RTv0897BTXm3x595lC0X/g1f13m7IImzLs2/lNT43zH9ILMwVnWk8WzMbaSSJ\n"
        "tVdmaM2MExwMUgem1XEx/Fb5ucA1BgvXbJ9a2SY21VQ/n4WwqAdgjR3UoBZR2Dje\n"
        "Zg38Sia+Ripmigopapm5zdOJCvkv1qdvK1uV4d357qGxd26S1N1E59YZ5+xliK93\n"
        "g16q9wXNTNDnwtbW4jtirU2VwTelLKafd6pv648oSpjVbsCMA0WbL99QPd+7JRwh\n"
        "vwIDAQAB\n"
        "-----END PUBLIC KEY-----"
    )
