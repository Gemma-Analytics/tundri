import logging
import os
import subprocess
from typing import Dict, Type, T
from pathlib import Path

from dotenv import load_dotenv, dotenv_values

from rich.console import Console
from rich.logging import RichHandler
from snowflake.connector import connect

from tundri.constants import STRING_CASING_CONVERSION_MAP


logging.basicConfig(
    level="WARN", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)
log.setLevel("INFO")
console = Console()


class ConfigurationError(Exception):
    pass


def load_env_var(path_to_env: str):
    """
    Loads environment variables from a dotenv file.
    Dotenv file has to live in the same directory as the Permifrost specifications file.
    If an evironment variable with the same name already exists in on the system (e.g., 
    in .bashrc), the existing variable is overwritten with the corresponding value from
    the dotenv file. Filename has to be ".env".

    :param path_to_env: Path to .env file
    :return: --
    """
    console.log("[bold][purple]Loading environment variables [/purple] started[/bold]")
    path_to_dotenv = (
        Path(path_to_env)
        .resolve()  # Converts relative to absolute path
        .parent  # Drop filename, and only retain dir from path
    )
    path_to_dotenv = path_to_dotenv / ".env"
    
    console.log(f"Checking for [italic]{str(path_to_dotenv)}[/italic]")
    if path_to_dotenv.is_file():
        console.log("Found dotenv file in directory; parsing")
        env_var = dotenv_values(path_to_dotenv)  # Dump the contents of .env in a variable
        if not env_var:
            console.log("Dotenv file is empty, nothing to parse")
            console.log("Using system's environment variables instead")
        else:
            console.log("Loading the following environment variables from dotenv:")
            for key, value in env_var.items():
                console.log(f"{key}={value}")
            console.log(
                "\nThe following environment variables already exist on the system " + 
                "and will be overwritten with the contents of the dotenv file:"
            )
            for key, value in env_var.items():
                this_value = os.environ.get(key)
                if this_value != None:
                    console.log(f"{key}={this_value}")
            load_dotenv(path_to_dotenv, override=True)
    else:
        console.log(f"Could not find dotenv file under {str(path_to_dotenv)}")
        console.log("Using system's environment variables instead")


def get_configs() -> Dict[str, str]:
    """Get the configuration from environment variables and validate them before returning"""
    config = {
        "user": os.getenv("PERMISSION_BOT_USER"),
        "password": os.getenv("PERMISSION_BOT_PASSWORD", ""),
        "account": os.getenv("PERMISSION_BOT_ACCOUNT"),
        "database": os.getenv("PERMISSION_BOT_DATABASE"),
        "role": os.getenv("PERMISSION_BOT_ROLE"),
        "warehouse": os.getenv("PERMISSION_BOT_WAREHOUSE"),
        "key_path": os.getenv("PERMISSION_BOT_KEY_PATH"),
        "key_passphrase": os.getenv("PERMISSION_BOT_KEY_PASSPHRASE"),
    }

    if not config["account"]:
        raise ConfigurationError(
            "The PERMISSION_BOT_ACCOUNT environment variable is not set"
        )
    if not config["database"]:
        raise ConfigurationError(
            "The PERMISSION_BOT_DATABASE environment variable is not set"
        )
    if not config["user"]:
        raise ConfigurationError(
            "The PERMISSION_BOT_USER environment variable is not set"
        )
    if not config["warehouse"]:
        raise ConfigurationError(
            "The PERMISSION_BOT_WAREHOUSE environment variable is not set"
        )

    return config


def get_snowflake_cursor():
    """Get a Snowflake cursor with support for private key authentication"""
    config = get_configs()
    connection_params = {
        "user": config["user"],
        "account": config["account"],
        "warehouse": config["warehouse"],
        "database": config["database"],
    }

    if config["key_path"] is not None:
        connection_params = {
            **connection_params,
            "private_key_file": config["key_path"],
            "private_key_file_pwd": config["key_passphrase"],
        }
    else:
        connection_params = {
            **connection_params,
            "password": config["password"],
        }

    return connect(**connection_params).cursor()


def plural(name: str) -> str:
    return f"{name}s"


def format_metadata_value(name: str, value):
    """
    Format metadata values read from the YAML file or Snowflake metadata

    Most values are converted to lowercase to simplify comparisons, but other parameters
    like `rsa_public_key` are treated differently as defined in `STRING_CASING_CONVERSION_MAP`
    """
    if isinstance(value, str):
        str_callable = STRING_CASING_CONVERSION_MAP.get(name, str.lower)
        value = str_callable(value.strip())
        if value.casefold() == "true":
            return True
        if value.casefold() == "false":
            return False
        return value
    return value


def format_params(params: Dict) -> str:
    """Returns formated list of parameters to use as arguments in DDL statements"""

    def get_param_value_type(value: str) -> Type[T]:
        if not isinstance(value, str):
            value = str(value)
        if value.isdigit():
            return int
        if value.upper() in ["TRUE", "FALSE"]:
            return bool
        return str

    params_formatted = []
    templates = {
        int: "{name} = {value}",
        bool: "{name} = {value}",
        str: "{name} = '{value}'",
    }
    for name, value in params.items():
        value_type = get_param_value_type(value)
        # Workaround to ensure Snowflake accepts default_role, default_warehouse and
        # default_namespace when quoted as alter statement parameters
        if name.lower() in ["default_role", "default_warehouse", "default_namespace"]:
            value = value.upper()
        params_formatted.append(templates[value_type].format(name=name, value=value))
    return ", ".join(params_formatted)


def run_command(command):
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Continuously read and print output
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            console.log(output.strip())

    # Check for errors
    output, errs = process.communicate()
    if process.returncode != 0:
        console.log(f"Error: {errs.strip()}")
        raise subprocess.CalledProcessError(process.returncode, command, errs)
    return output, errs


def log_dry_run_info():
    console.log(20 * "-")
    console.log("[bold]Executing in [yellow]dry run mode[/yellow][/bold]")
    console.log(20 * "-")
