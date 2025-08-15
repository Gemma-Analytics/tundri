import pytest
import os

from permifrost.snowflake_spec_loader import SnowflakeSpecLoader
from permifrost_test_utils.snowflake_schema_builder import (
    SnowflakeSchemaBuilder,
)
from permifrost_test_utils.snowflake_connector import MockSnowflakeConnector

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SPEC_FILE_DIR = os.path.join(THIS_DIR, "specs")
SCHEMA_FILE_DIR = os.path.join(THIS_DIR, "schemas")


def get_spec_from_file(file_name):
    with open(os.path.join(SPEC_FILE_DIR, file_name), "r") as fd:
        spec_data = fd.read()
    return spec_data


@pytest.fixture
def test_dir(request):
    return request.fspath.dirname


@pytest.fixture
def mock_connector():
    return MockSnowflakeConnector()


@pytest.fixture
def test_roles_spec_file():
    """Semi-robust spec file for testing user properties."""
    spec_file_data = (
        SnowflakeSchemaBuilder()
        .add_user(name="base_user_test")
        .add_user(name="test_user_with_password_disabled", has_password=False)
        .add_user(name="test_user_with_display_name", display_name="Gaius")
        .add_user(name="test_user_with_comment", comment="I am a comment")
        .add_user(
            name="test_user_with_comment_password_disabled",
            has_password=False,
            comment="I am a comment",
        )
        .add_user(
            name="test_user_defaults",
            default_warehouse="ftl",
            default_namespace="public",
            default_role="role1",
        )
        .add_user(
            name="test_user_with_password_display_name_comment",
            has_password=True,
            display_name="Boomer",
            comment="Please do not disable the password, for some reason can not proceed after the CAPTCHA.",
        )
        .add_user(
            name="test_user_with_full_name",
            first_name="Kara",
            middle_name="Starbuck",
            last_name="Thrace",
        )
        .add_user(name="test_user_with_email", email="It is not validated")
        .add_user(
            name="test_user_with_multiple_properties",
            has_password=False,
            display_name="Husker",
            first_name="William",
            middle_name="Bill",
            last_name="Adama",
            email="wba@bsg.com",
            comment="Not a Cylon",
        )
        .build()
    )
    yield spec_file_data


@pytest.fixture()
def test_roles_mock_connector(mocker):
    """Mock connector for use in testing  user properties."""

    mock_connector = MockSnowflakeConnector()
    mocker.patch.object(
        mock_connector,
        "show_users",
        return_value=[
            "base_user_test",
            "test_user_with_password_disabled",
            "test_user_with_display_name",
            "test_user_with_comment",
            "test_user_with_comment_password_disabled",
            "test_user_with_password_display_name_comment",
            "test_user_defaults",
            "test_user_with_full_name",
            "test_user_with_email",
            "test_user_with_multiple_properties",
        ],
    )
    yield mock_connector


class TestSnowflakeUserProperties:
    def test_user_base(
        self, mocker, test_roles_mock_connector, test_roles_spec_file
    ):
        """Make sure that the user without any property only have the DISABLED property altered"""

        print(f"Spec File Data is:\n{test_roles_spec_file}")
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=test_roles_spec_file)
        )
        spec_loader = SnowflakeSpecLoader(
            spec_path="", conn=test_roles_mock_connector
        )
        queries = spec_loader.generate_permission_queries(
            users=["base_user_test"], run_list=["users"]
        )
        assert queries == [
            {
                "already_granted": False,
                "sql": "ALTER USER base_user_test SET DISABLED = FALSE",
            }
        ]

    def test_user_with_password_disabled(
        self, mocker, test_roles_mock_connector, test_roles_spec_file
    ):
        """Make sure that the user password get set to null if the has_password property is False"""

        print(f"Spec File Data is:\n{test_roles_spec_file}")
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=test_roles_spec_file)
        )
        spec_loader = SnowflakeSpecLoader(
            spec_path="", conn=test_roles_mock_connector
        )
        queries = spec_loader.generate_permission_queries(
            users=["test_user_with_password_disabled"], run_list=["users"]
        )
        assert queries == [
            {
                "already_granted": False,
                "sql": "ALTER USER test_user_with_password_disabled SET DISABLED = FALSE, PASSWORD = NULL",
            }
        ]

    def test_user_with_display_name(
        self, mocker, test_roles_mock_connector, test_roles_spec_file
    ):
        """Make sure that the user display_name get set if the display_name property is set"""

        print(f"Spec File Data is:\n{test_roles_spec_file}")
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=test_roles_spec_file)
        )
        spec_loader = SnowflakeSpecLoader(
            spec_path="", conn=test_roles_mock_connector
        )
        queries = spec_loader.generate_permission_queries(
            users=["test_user_with_display_name"], run_list=["users"]
        )

        assert queries == [
            {
                "already_granted": False,
                "sql": "ALTER USER test_user_with_display_name SET DISABLED = FALSE, DISPLAY_NAME = 'Gaius'",
            }
        ]

    def test_user_with_comment(
        self, mocker, test_roles_mock_connector, test_roles_spec_file
    ):
        """Make sure that the user COMMENT get set if the comment property is set"""

        print(f"Spec File Data is:\n{test_roles_spec_file}")
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=test_roles_spec_file)
        )
        spec_loader = SnowflakeSpecLoader(
            spec_path="", conn=test_roles_mock_connector
        )
        queries = spec_loader.generate_permission_queries(
            users=["test_user_with_comment"], run_list=["users"]
        )

        assert queries == [
            {
                "already_granted": False,
                "sql": "ALTER USER test_user_with_comment SET DISABLED = FALSE, COMMENT = 'I am a comment'",
            }
        ]

    def test_user_with_comment_password_disabled(
        self, mocker, test_roles_mock_connector, test_roles_spec_file
    ):
        """Make sure if multiple properties is set (PASSWORD, COMMENT) then all if them are set."""

        print(f"Spec File Data is:\n{test_roles_spec_file}")
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=test_roles_spec_file)
        )
        spec_loader = SnowflakeSpecLoader(
            spec_path="", conn=test_roles_mock_connector
        )
        queries = spec_loader.generate_permission_queries(
            users=["test_user_with_comment_password_disabled"],
            run_list=["users"],
        )

        assert queries == [
            {
                "already_granted": False,
                "sql": "ALTER USER test_user_with_comment_password_disabled SET DISABLED = FALSE, PASSWORD = NULL, COMMENT = 'I am a comment'",
            }
        ]

    def test_user_with_full_name(
        self, mocker, test_roles_mock_connector, test_roles_spec_file
    ):
        """Make sure if multiple properties is set (FIRST_NAME, MIDDLE_NAME, LAST_NAME) then all if them are set."""

        print(f"Spec File Data is:\n{test_roles_spec_file}")
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=test_roles_spec_file)
        )
        spec_loader = SnowflakeSpecLoader(
            spec_path="", conn=test_roles_mock_connector
        )
        queries = spec_loader.generate_permission_queries(
            users=["test_user_with_full_name"], run_list=["users"]
        )

        assert queries == [
            {
                "already_granted": False,
                "sql": "ALTER USER test_user_with_full_name SET DISABLED = FALSE, FIRST_NAME = 'Kara', "
                "MIDDLE_NAME = 'Starbuck', LAST_NAME = 'Thrace'",
            }
        ]

    def test_user_with_email(
        self, mocker, test_roles_mock_connector, test_roles_spec_file
    ):
        """Make sure if the EMAIL property is set then the EMAIL is set."""

        print(f"Spec File Data is:\n{test_roles_spec_file}")
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=test_roles_spec_file)
        )
        spec_loader = SnowflakeSpecLoader(
            spec_path="", conn=test_roles_mock_connector
        )
        queries = spec_loader.generate_permission_queries(
            users=["test_user_with_email"], run_list=["users"]
        )

        assert queries == [
            {
                "already_granted": False,
                "sql": "ALTER USER test_user_with_email SET DISABLED = FALSE, EMAIL = 'It is not validated'",
            }
        ]

    def test_user_with_password_display_name_comment(
        self, mocker, test_roles_mock_connector, test_roles_spec_file
    ):
        """Make sure if multiple properties is set (DISPLAY_NAME, COMMENT) then all if them are set."""

        print(f"Spec File Data is:\n{test_roles_spec_file}")
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=test_roles_spec_file)
        )
        spec_loader = SnowflakeSpecLoader(
            spec_path="", conn=test_roles_mock_connector
        )
        queries = spec_loader.generate_permission_queries(
            users=["test_user_with_password_display_name_comment"],
            run_list=["users"],
        )

        assert queries == [
            {
                "already_granted": False,
                "sql": "ALTER USER test_user_with_password_display_name_comment SET DISABLED = FALSE, "
                "DISPLAY_NAME = 'Boomer', "
                "COMMENT = 'Please do not disable the password, for some reason can not proceed after the CAPTCHA.'",
            }
        ]

    def test_user_with_multiple_properties(
        self, mocker, test_roles_mock_connector, test_roles_spec_file
    ):
        """Make sure if multiple properties is set (PASSWORD, DISPLAY_NAME,FIRST_NAME,MIDDLE_NAME,LAST_NAME,
        EMAIL COMMENT) then all if them are set."""

        print(f"Spec File Data is:\n{test_roles_spec_file}")
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=test_roles_spec_file)
        )
        spec_loader = SnowflakeSpecLoader(
            spec_path="", conn=test_roles_mock_connector
        )
        queries = spec_loader.generate_permission_queries(
            users=["test_user_with_multiple_properties"], run_list=["users"]
        )

        assert queries == [
            {
                "already_granted": False,
                "sql": "ALTER USER test_user_with_multiple_properties SET DISABLED = FALSE, "
                "PASSWORD = NULL, "
                "DISPLAY_NAME = 'Husker', "
                "FIRST_NAME = 'William', "
                "MIDDLE_NAME = 'Bill', "
                "LAST_NAME = 'Adama', "
                "EMAIL = 'wba@bsg.com', "
                "COMMENT = 'Not a Cylon'",
            }
        ]

    def test_user_defaults(
        self, mocker, test_roles_mock_connector, test_roles_spec_file
    ):
        """Make sure if multiple properties is set (DEFAULT_WAREHOUSE, DEFAULT_NAMESPACE,DEFAULT_ROLE)
        then all if them are set."""

        print(f"Spec File Data is:\n{test_roles_spec_file}")
        mocker.patch(
            "builtins.open", mocker.mock_open(read_data=test_roles_spec_file)
        )
        spec_loader = SnowflakeSpecLoader(
            spec_path="", conn=test_roles_mock_connector
        )
        queries = spec_loader.generate_permission_queries(
            users=["test_user_defaults"], run_list=["users"]
        )

        assert queries == [
            {
                "already_granted": False,
                "sql": "ALTER USER test_user_defaults SET DISABLED = FALSE, "
                "DEFAULT_WAREHOUSE = 'ftl', "
                "DEFAULT_NAMESPACE = 'public', "
                "DEFAULT_ROLE = 'role1'",
            }
        ]
