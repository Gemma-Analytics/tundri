import argparse
import logging
import sys

from rich.console import Console
from rich.logging import RichHandler

from tundri.core import drop_create_objects
from tundri.utils import (
    run_command,
    log_dry_run_info,
    load_env_var
)


logging.basicConfig(
    level="WARN", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)
log.setLevel("INFO")
console = Console()


def drop_create(args):
    console.log("[bold][purple]Drop/create Snowflake objects[/purple] started[/bold]")
    if args.dry:
        log_dry_run_info()
    is_success = drop_create_objects(args.permifrost_spec_path, args.dry)
    if is_success:
        console.log(
            "[bold][purple]\nDrop/create Snowflake objects[/purple] completed successfully[/bold]\n"
        )
    else:
        sys.exit(1)


def permifrost(args):
    console.log("[bold][purple]Permifrost[/purple] started[/bold]")
    cmd = [
        "permifrost",
        "run",
        args.permifrost_spec_path,
        "--ignore-missing-entities-dry-run",
    ]

    if args.dry:
        cmd.append("--dry")
        log_dry_run_info()

    console.log(f"Running command: \n[italic]{' '.join(cmd)}[/italic]\n")
    run_command(cmd)
    console.log("[bold][purple]Permifrost[/purple] completed successfully[bold]\n")


def run(args):
    drop_create(args)
    permifrost(args)


def main():
    parser = argparse.ArgumentParser(
        description="Snowflake Manager - Drop, create and alter Snowflake objects and set permissions with Permifrost"
    )
    subparsers = parser.add_subparsers()

    # Drop/create functionality
    parser_drop_create = subparsers.add_parser("drop_create")
    parser_drop_create.add_argument(
        "-p", "--permifrost_spec_path", "--filepath", required=True
    )
    parser_drop_create.add_argument("--dry", action="store_true")
    parser_drop_create.set_defaults(func=drop_create)

    # Permifrost functionality
    parser_drop_create = subparsers.add_parser("permifrost")
    parser_drop_create.add_argument(
        "-p", "--permifrost_spec_path", "--filepath", required=True
    )
    parser_drop_create.add_argument("--dry", action="store_true")
    parser_drop_create.set_defaults(func=permifrost)

    # Run both
    parser_drop_create = subparsers.add_parser("run")
    parser_drop_create.add_argument(
        "-p", "--permifrost_spec_path", "--filepath", required=True
    )
    parser_drop_create.add_argument("--dry", action="store_true")
    parser_drop_create.set_defaults(func=run)

    args = parser.parse_args()
    # Loading .env here, because function needs access to the path to config .yml, as
    # the .env is expected to live in the same directory as the .yml
    load_env_var(args.permifrost_spec_path)
    args.func(args)


if __name__ == "__main__":
    main()
