# Tundri Output Cleanup Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up tundri's console output — remove noise (timestamps, line refs), rename the scary "Drop/create" header, add a DDL summary line with operation counts, condense env loading, and consolidate the dry-run banner.

**Architecture:** Replace all `console.log()` calls with `console.print()` and remove dead logging framework imports. Restructure output format in `cli.py`, `core.py`, `utils.py`, and `inspector.py`. Add a `build_summary_line()` function in `core.py` to count operations by type.

**Tech Stack:** Python, Rich (console.print markup)

**Spec:** `docs/superpowers/specs/2026-03-13-output-cleanup-design.md`

**Sandbox for validation:** `/home/lui/projects/internal/gemma-sandbox-snowflake`

---

## Chunk 1: Logging cleanup and mechanical replacements

### Task 1: Remove dead logging framework and replace console.log → console.print in utils.py

**Files:**
- Modify: `tundri/utils.py:1-26` (imports and logging setup)
- Modify: `tundri/utils.py:44-74` (load_env_var)
- Modify: `tundri/utils.py:196-209` (run_command, log_dry_run_info)

- [ ] **Step 1: Remove dead logging imports and setup in utils.py**

Replace lines 1-22:
```python
import os
import subprocess
from typing import Dict, Type, TypeVar, List
from pathlib import Path

from dotenv import load_dotenv, dotenv_values

from rich.console import Console
from snowflake.connector import connect
from snowflake.connector.cursor import SnowflakeCursor

from tundri.constants import STRING_CASING_CONVERSION_MAP, INSPECTOR_ROLE


console = Console()

# Suppress urllib3 connection warnings from Snowflake connector
import logging
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logging.getLogger("snowflake.connector.vendored.urllib3.connectionpool").setLevel(logging.ERROR)
```

Note: We keep `import logging` only for the urllib3 suppression lines — those are needed to prevent noisy connection warnings from the Snowflake connector. Also fix the pre-existing `from typing import T` (invalid — `T` does not exist in `typing`) by importing `TypeVar` instead. Add `T = TypeVar("T")` after the imports if needed by `format_params`, or remove the `Type[T]` annotation entirely since it's only used in a local helper.

- [ ] **Step 2: Replace all console.log → console.print in utils.py**

Mechanical replacement of every `console.log(` with `console.print(` in utils.py (~12 occurrences at lines 44, 52, 54, 57, 58, 60, 62, 63, 70, 73, 74, 196, 201, 207, 208, 209).

- [ ] **Step 3: Run tests**

Run: `cd /home/lui/projects/internal/tundri && uv run pytest tests/test_utils.py -v`
Expected: All tests PASS (test_plural, test_treat_metadata_value, test_format_params — none depend on console output)

- [ ] **Step 4: Commit**

```bash
git add tundri/utils.py
git commit -m "refactor: remove dead logging framework, console.log → console.print in utils"
```

### Task 2: Remove dead logging framework and replace console.log → console.print in core.py

**Files:**
- Modify: `tundri/core.py:1-75` (imports and logging setup)
- Modify: `tundri/core.py:117-144` (print_ddl_statements, execute_ddl)
- Modify: `tundri/core.py:200` (resolve_objects)
- Modify: `tundri/core.py:329-361` (drop_create_objects)

- [ ] **Step 1: Remove dead logging imports and setup in core.py**

Surgical removals (do NOT replace the entire import block — keep all `from tundri.*` imports intact):

1. Remove `import logging` (line 1)
2. Remove `from rich.logging import RichHandler` (line 6)
3. Remove the `logging.basicConfig(...)` block (lines 70-72)
4. Remove `log = logging.getLogger(__name__)` (line 73)
5. Remove `log.setLevel("INFO")` (line 74)

The result is that lines 2-5, 7-8, and 10-67 remain unchanged. Line 75 (`console = Console()`) already exists and stays.

- [ ] **Step 2: Replace all console.log → console.print in core.py**

Mechanical replacement of every `console.log(` with `console.print(` in core.py (~14 occurrences at lines 120, 127, 128, 138, 144, 200, 329, 335, 341, 348, 349, 353, 360, 361).

- [ ] **Step 3: Run tests**

Run: `cd /home/lui/projects/internal/tundri && uv run pytest tests/test_core.py -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add tundri/core.py
git commit -m "refactor: remove dead logging framework, console.log → console.print in core"
```

### Task 3: Remove dead logging framework and replace console.log → console.print in inspector.py and cli.py

**Files:**
- Modify: `tundri/inspector.py:1-33` (imports and logging setup)
- Modify: `tundri/inspector.py:108-112` (warning message)
- Modify: `tundri/cli.py:1-21` (imports and logging setup)
- Modify: `tundri/cli.py:25-54` (all console.log calls)

- [ ] **Step 1: Remove dead logging imports and setup in inspector.py**

Replace lines 1-33:
```python
from pprint import pprint
from typing import FrozenSet, List

from rich.console import Console

from tundri.constants import OBJECT_TYPES, OBJECT_TYPE_MAP, INSPECTOR_ROLE
from tundri.objects import SnowflakeObject, Schema, User
from tundri.utils import (
    plural,
    get_snowflake_cursor,
    format_metadata_value,
    get_existing_user,
)

from snowflake.connector.errors import ProgrammingError

# Column names of SHOW statement are different than parameter names in DDL statements
parameter_name_map = {
    "warehouse": {
        "size": "warehouse_size",
        "type": "warehouse_type",
    },
}


console = Console()
```

- [ ] **Step 2: Update inspector warning format and replace console.log → console.print**

Replace the warning at lines 108-112:
```python
                    console.print(
                        f"[yellow]Warning:[/yellow] Skipping metadata retrieval"
                        f" for user {user}: Permifrost user doesn't have DESCRIBE"
                        " privileges on this object"
                    )
```

- [ ] **Step 3: Remove dead logging imports and setup in cli.py**

Replace lines 1-21:
```python
import argparse
import sys

from rich.console import Console

from tundri.core import drop_create_objects
from tundri.utils import (
    run_command,
    log_dry_run_info,
    load_env_var
)


console = Console()
```

- [ ] **Step 4: Replace all console.log → console.print in cli.py**

Mechanical replacement of every `console.log(` with `console.print(` in cli.py (~7 occurrences at lines 25, 32, 40, 52, 54).

Also fix the unclosed markup tag at line 54:
```python
    console.print("[bold][purple]Permifrost[/purple] completed successfully[/bold]\n")
```

- [ ] **Step 5: Run all tests**

Run: `cd /home/lui/projects/internal/tundri && uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 6: Run dry-run against sandbox to verify no timestamps/line refs**

Run: `cd /home/lui/projects/internal/gemma-sandbox-snowflake && uv run --project /home/lui/projects/internal/tundri tundri run --dry -p permifrost.yml 2>&1 | head -40`
Expected: Output lines have NO `[HH:MM:SS]` timestamps on the left and NO `file.py:line` references on the right.

- [ ] **Step 7: Commit**

```bash
git add tundri/inspector.py tundri/cli.py
git commit -m "refactor: remove dead logging framework, console.log → console.print in inspector and cli"
```

---

## Chunk 2: Output format restructuring

### Task 4: Rename section header from "Drop/create" to "Manage"

**Files:**
- Modify: `tundri/cli.py:25` (started message)
- Modify: `tundri/cli.py:32-34` (completed message)

- [ ] **Step 1: Rename section headers in cli.py**

In `drop_create()`:
```python
    console.print("[bold][purple]Manage Snowflake objects[/purple] started[/bold]")
```

And the completed message:
```python
        console.print(
            "[bold][purple]\nManage Snowflake objects[/purple] completed successfully[/bold]\n"
        )
```

- [ ] **Step 2: Run dry-run against sandbox to verify**

Run: `cd /home/lui/projects/internal/gemma-sandbox-snowflake && uv run --project /home/lui/projects/internal/tundri tundri run --dry -p permifrost.yml 2>&1 | grep -i "manage\|drop/create"`
Expected: See "Manage Snowflake objects", no "Drop/create"

- [ ] **Step 3: Commit**

```bash
git add tundri/cli.py
git commit -m "refactor: rename 'Drop/create' section header to 'Manage Snowflake objects'"
```

### Task 5: Consolidate dry-run banner to single top-level call

**Files:**
- Modify: `tundri/utils.py:206-209` (log_dry_run_info function)
- Modify: `tundri/cli.py` (move banner call, remove per-section calls)

- [ ] **Step 1: Update log_dry_run_info() in utils.py**

Replace the function body:
```python
def log_dry_run_info():
    console.print("[bold][yellow]⚠ DRY RUN — no changes will be applied[/yellow][/bold]\n")
```

- [ ] **Step 2: Move dry-run banner to top of execution in cli.py**

In `main()`, add the dry-run banner **before** `load_env_var()` so it appears at the very top of the output (matching the spec's target output order: banner → env loading → manage objects).

At `cli.py`, after `args = parser.parse_args()` (line 113) and **before** `load_env_var(args.permifrost_spec_path)` (line 116):
```python
    if args.dry:
        log_dry_run_info()
```

Remove the `if args.dry: log_dry_run_info()` calls from:
- `drop_create()` (lines 26-27)
- `permifrost()` (lines 48-50)

- [ ] **Step 3: Run dry-run against sandbox to verify single banner**

Run: `cd /home/lui/projects/internal/gemma-sandbox-snowflake && uv run --project /home/lui/projects/internal/tundri tundri run --dry -p permifrost.yml 2>&1 | grep -c "DRY RUN"`
Expected: `1` (appears exactly once)

- [ ] **Step 4: Commit**

```bash
git add tundri/utils.py tundri/cli.py
git commit -m "refactor: consolidate dry-run banner to single top-level call"
```

### Task 6: Condense environment variable loading output

**Files:**
- Modify: `tundri/utils.py:33-74` (load_env_var function)

- [ ] **Step 1: Rewrite load_env_var() output**

Replace the function body (keeping the same logic, just changing output):
```python
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
    path_to_dotenv = (
        Path(path_to_env)
        .resolve()  # Converts relative to absolute path
        .parent  # Drop filename, and only retain dir from path
    )
    path_to_dotenv = path_to_dotenv / ".env"

    if path_to_dotenv.is_file():
        env_var = dotenv_values(path_to_dotenv)
        if not env_var:
            console.print("Empty .env file, using system environment variables")
        else:
            load_dotenv(path_to_dotenv, override=True)
            console.print(f"Loaded {len(env_var)} environment variables from [italic]{str(path_to_dotenv)}[/italic]\n")
    else:
        console.print(f"No .env file found, using system environment variables")
```

- [ ] **Step 2: Run dry-run against sandbox to verify condensed output**

Run: `cd /home/lui/projects/internal/gemma-sandbox-snowflake && uv run --project /home/lui/projects/internal/tundri tundri run --dry -p permifrost.yml 2>&1 | head -10`
Expected: See a single "Loaded N environment variables from ..." line, no individual variable listings

- [ ] **Step 3: Commit**

```bash
git add tundri/utils.py
git commit -m "refactor: condense env var loading to single summary line"
```

---

## Chunk 3: DDL summary line

### Task 7: Write tests for the summary line builder

**Files:**
- Modify: `tests/test_core.py`

- [ ] **Step 1: Write failing tests for build_summary_line()**

Add to `tests/test_core.py`:
```python
from tundri.core import build_summary_line


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
    """Only ALTER SET — no UNSET breakdown needed when all are SET."""
    statements = [
        "USE ROLE SECURITYADMIN",
        "ALTER USER foo SET rsa_public_key='...'",
    ]
    result = build_summary_line(statements)
    assert result == "0 CREATE, 1 ALTER (1 SET), 0 DROP"


def test_build_summary_line_only_alters_unset():
    """Only ALTER UNSET."""
    statements = [
        "USE ROLE SECURITYADMIN",
        "ALTER USER foo UNSET rsa_public_key",
    ]
    result = build_summary_line(statements)
    assert result == "0 CREATE, 1 ALTER (1 UNSET), 0 DROP"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/lui/projects/internal/tundri && uv run pytest tests/test_core.py::test_build_summary_line_mixed_operations -v`
Expected: FAIL with `ImportError: cannot import name 'build_summary_line'`

- [ ] **Step 3: Commit**

```bash
git add tests/test_core.py
git commit -m "test: add failing tests for DDL summary line builder"
```

### Task 8: Implement build_summary_line() and integrate into output

**Files:**
- Modify: `tundri/core.py` (add build_summary_line function)
- Modify: `tundri/core.py:117-128` (update print_ddl_statements)

- [ ] **Step 1: Add build_summary_line() to core.py**

Add after the `build_statements_list` function (after line 114):
```python
def build_summary_line(statements: List) -> str | None:
    """Build a summary line showing counts of each DDL operation type.

    Parses statement strings to classify operations. USE ROLE statements are skipped.
    ALTER statements are sub-classified as SET or UNSET by checking for ' UNSET '.

    Returns:
        Summary string like '3 CREATE, 2 ALTER (1 SET, 1 UNSET), 0 DROP', or None if empty.
    """
    if not statements:
        return None

    create_count = 0
    drop_count = 0
    alter_set_count = 0
    alter_unset_count = 0

    for s in statements:
        if s.startswith("USE ROLE"):
            continue
        if s.startswith("CREATE"):
            create_count += 1
        elif s.startswith("DROP"):
            drop_count += 1
        elif s.startswith("ALTER"):
            if " UNSET " in s:
                alter_unset_count += 1
            else:
                alter_set_count += 1

    alter_total = alter_set_count + alter_unset_count
    if alter_total > 0:
        alter_parts = []
        if alter_set_count > 0:
            alter_parts.append(f"{alter_set_count} SET")
        if alter_unset_count > 0:
            alter_parts.append(f"{alter_unset_count} UNSET")
        alter_str = f"{alter_total} ALTER ({', '.join(alter_parts)})"
    else:
        alter_str = "0 ALTER"

    drop_str = f"{drop_count} DROP"

    return f"{create_count} CREATE, {alter_str}, {drop_str}"
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /home/lui/projects/internal/tundri && uv run pytest tests/test_core.py -v`
Expected: All tests PASS (including the 5 new summary line tests)

- [ ] **Step 3: Update print_ddl_statements() to show summary and color DROPs**

Replace the `print_ddl_statements` function:
```python
def print_ddl_statements(statements: List) -> None:
    """Print DDL statements to be executed with a summary line."""
    if not statements:
        console.print(
            "No statements to execute (the state of Snowflake objects matches the Permifrost spec)\n"
        )
        return

    summary = build_summary_line(statements)
    drop_count = sum(1 for s in statements if s.startswith("DROP"))
    if drop_count > 0:
        # Highlight DROP count in red within the summary
        summary = summary.replace(f"{drop_count} DROP", f"[red]{drop_count} DROP[/red]")
    console.print(summary)
    console.print()

    for s in statements:
        if s.startswith("USE ROLE"):
            continue
        if s.startswith("DROP"):
            console.print(f"[red]- {s}[/red]")
        else:
            console.print(f"[italic]- {s}[/italic]")
    console.print()
```

- [ ] **Step 4: Run dry-run against sandbox to verify summary line**

Run: `cd /home/lui/projects/internal/gemma-sandbox-snowflake && uv run --project /home/lui/projects/internal/tundri tundri run --dry -p permifrost.yml 2>&1 | head -30`
Expected: See the summary line (e.g. `0 CREATE, 23 ALTER (0 SET, 23 UNSET), 0 DROP`) before the statement list

- [ ] **Step 5: Run all tests**

Run: `cd /home/lui/projects/internal/tundri && uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add tundri/core.py tests/test_core.py
git commit -m "feat: add DDL summary line with operation counts and red DROP highlighting"
```

---

## Chunk 4: Final validation and documentation alignment

### Task 9: Full end-to-end validation

**Files:** None (validation only)

- [ ] **Step 1: Run all tests**

Run: `cd /home/lui/projects/internal/tundri && uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 2: Run dry-run against sandbox and verify full output format**

Run: `cd /home/lui/projects/internal/gemma-sandbox-snowflake && uv run --project /home/lui/projects/internal/tundri tundri run --dry -p permifrost.yml 2>&1`

Verify the following against the target output in the spec:
1. No timestamps or file:line references on any line
2. Single `⚠ DRY RUN` banner at the top
3. Single `Loaded N environment variables from ...` line
4. `Manage Snowflake objects started` (not "Drop/create")
5. `Warning:` prefix on inspector warnings (not `WARNING`)
6. Summary line before DDL statements (e.g. `0 CREATE, N ALTER (0 SET, N UNSET), 0 DROP`)
7. `Manage Snowflake objects completed successfully`
8. `Permifrost started` / `Permifrost completed successfully`

- [ ] **Step 3: Run a normal (non-dry) run against sandbox to verify execution path**

Run: `cd /home/lui/projects/internal/gemma-sandbox-snowflake && uv run --project /home/lui/projects/internal/tundri tundri run -p permifrost.yml 2>&1`

Verify the output still works correctly for the execution path (account confirmation prompt, DDL execution with checkmarks, etc.)

### Task 10: Documentation terminology alignment

**Files:**
- Modify: `tundri/cli.py` (argparse descriptions)
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update argparse descriptions in cli.py**

Update the main parser description:
```python
    parser = argparse.ArgumentParser(
        description="tundri - Manage Snowflake objects and set permissions with Permifrost"
    )
```

Update the `drop_create` subparser help:
```python
    parser_drop_create = subparsers.add_parser("drop_create", help="Manage Snowflake objects (create, drop, alter)")
```

- [ ] **Step 2: Update CLAUDE.md terminology**

In the "What is Tundri" section, replace references to "DROP/CREATE/ALTER" with "manage" where appropriate. In the "Architecture" section, update the execution flow to say "Manage: generate DROP, CREATE, ALTER statements" instead of "Compare: generate DROP, CREATE, ALTER statements". Update the `drop_create` subcommand description in the commands section.

- [ ] **Step 3: Run all tests one final time**

Run: `cd /home/lui/projects/internal/tundri && uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add tundri/cli.py CLAUDE.md
git commit -m "docs: align terminology with 'Manage Snowflake objects' naming"
```
