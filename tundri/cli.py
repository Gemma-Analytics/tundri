import argparse
import sys

from rich.console import Console

from tundri.core import manage_objects
from tundri.utils import load_env_var, log_dry_run_info, run_command

console = Console()


def manage(args):
    console.print("[bold][purple]Manage Snowflake objects[/purple] started[/bold]")
    if args.dry:
        log_dry_run_info()
    is_success = manage_objects(args.permifrost_spec_path, args.dry, args.users_to_skip)
    if is_success:
        console.print(
            "[bold][purple]\nManage Snowflake objects[/purple]"
            " completed successfully[/bold]\n"
        )
    else:
        sys.exit(1)


# Keep drop_create as backwards-compatible alias
drop_create = manage


def permifrost(args):
    console.print("[bold][purple]Permifrost[/purple] started[/bold]")
    cmd = [
        "permifrost",
        "run",
        args.permifrost_spec_path,
        "--ignore-missing-entities-dry-run",
    ]

    if args.dry:
        cmd.append("--dry")
        log_dry_run_info()

    console.print(f"Running command: \n[italic]{' '.join(cmd)}[/italic]\n")
    run_command(cmd)
    console.print("[bold][purple]Permifrost[/purple] completed successfully[/bold]\n")


def run(args):
    manage(args)
    permifrost(args)


def main():
    parser = argparse.ArgumentParser(
        description="tundri - Manage Snowflake objects and set permissions"
    )
    subparsers = parser.add_subparsers()
    help_str_users_to_skip = """
        Users to ignore from object management operations
        (space-separated list, case-sensitive).
        Users with admin privileges can't be inspected by the permifrost user,
        because of them being higher in the role hierarchy than the default tundri
        inspector role. To avoid permission errors, skip those users during inspection.
        Altering skipped users through tundri won't work and needs to be done manually!
    """

    # Manage Snowflake objects (with drop_create as backwards-compatible alias)
    def add_manage_args(p):
        p.add_argument("-p", "--permifrost_spec_path", "--filepath", required=True)
        p.add_argument("--dry", action="store_true", help="Run in dry mode")
        p.add_argument(
            "--users-to-skip",
            nargs="+",
            metavar="USER_NAME",
            default=["admin", "snowflake", "auto_dba"],
            help=help_str_users_to_skip,
        )
        p.set_defaults(func=manage)

    parser_manage = subparsers.add_parser(
        "manage", help="Manage Snowflake objects (create, drop, alter)"
    )
    add_manage_args(parser_manage)

    parser_drop_create = subparsers.add_parser(
        "drop_create", help="Alias for 'manage' (deprecated)"
    )
    add_manage_args(parser_drop_create)

    # Permifrost functionality
    parser_permifrost = subparsers.add_parser("permifrost", help="Run Permifrost")
    parser_permifrost.add_argument(
        "-p", "--permifrost_spec_path", "--filepath", required=True
    )
    parser_permifrost.add_argument("--dry", action="store_true", help="Run in dry mode")
    parser_permifrost.set_defaults(func=permifrost)

    # Run both
    parser_run = subparsers.add_parser("run", help="Run manage and then permifrost")
    parser_run.add_argument("-p", "--permifrost_spec_path", "--filepath", required=True)
    parser_run.add_argument("--dry", action="store_true", help="Run in dry mode")
    parser_run.add_argument(
        "--users-to-skip",
        nargs="+",
        metavar="USER_NAME",
        default=["admin", "snowflake", "auto_dba"],
        help=help_str_users_to_skip,
    )
    parser_run.set_defaults(func=run)

    args = parser.parse_args()
    # Loading .env here, because function needs access to the path to config .yml, as
    # the .env is expected to live in the same directory as the .yml
    load_env_var(args.permifrost_spec_path)
    args.func(args)


if __name__ == "__main__":
    main()
