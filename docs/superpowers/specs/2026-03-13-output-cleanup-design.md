# Tundri Output Cleanup — Design Spec

**Date:** 2026-03-13
**Status:** Approved

## Problem

Tundri's console output is noisy and confusing:

1. **Timestamps and file:line references** on every line (from Rich's `console.log()`) provide no practical value and clutter the output.
2. **"Drop/create Snowflake objects"** section header is alarming — even when there are zero DROP statements, users think something destructive is happening.
3. **ALTER SET/UNSET operations** have no distinct identity in the output — they're lumped under "Drop/create" with no summary.
4. **Environment variable loading** is overly verbose (~20 lines before any real work starts).
5. **Dry-run banner** appears twice (once per section) using plain dashes — easy to miss.

## Approach

Refactor all `console.log()` calls to `console.print()` and restructure the output format. No new modules or abstractions — direct changes to existing files.

## Changes

### 1. Logging cleanup

- Remove dead code: `logging.basicConfig(...)`, `RichHandler` import, `log = logging.getLogger(...)` from all modules (`cli.py`, `core.py`, `utils.py`, `inspector.py`). The Python logging framework is configured but never used — all output goes through `console.log()`.
- Replace all `console.log(...)` with `console.print(...)` (~30 call sites). This is a mechanical find-and-replace — `console.print()` accepts the same parameters tundri uses (markup strings, `sep`, `end`).
- `Console()` constructor stays plain with no special flags.

**Why `console.print()` over `Console(log_time=False, log_path=False)`:** Even with flags disabled, `console.log()` still wraps every line in a `Table.grid` and walks the Python call stack on every invocation. `console.print()` renders content directly — simpler, no overhead.

### 2. Section header rename

- `"Drop/create Snowflake objects"` → `"Manage Snowflake objects"` in both "started" and "completed successfully" messages in `cli.py`.
- Same for the `drop_create` subcommand output.

### 3. Dry-run banner

- Remove the two separate `log_dry_run_info()` calls (one before object management, one before Permifrost).
- Add a single prominent banner at the very top of execution in `cli.py`, before anything else:

```
⚠ DRY RUN — no changes will be applied
```

- Yellow/bold styling, single line, no dashes.
- `log_dry_run_info()` function in `utils.py` updated with new styling and called once.

### 4. Environment variable loading

- Replace the current ~20 lines with a single summary line:

```
Loaded 7 environment variables from /path/to/.env
```

- Fallback: `No .env file found, using system environment variables`
- Empty file: `Empty .env file, using system environment variables`
- Error cases still print full details.

### 5. DDL statement summary and grouping

- Add a summary line before the flat list:

```
3 CREATE, 2 ALTER (1 SET, 1 UNSET), 0 DROP
```

- When DROP count > 0: DROP portion renders in red, DROP statements themselves print in red.
- Zero-count categories still appear in the summary (especially reassuring for `0 DROP`).
- Flat list below the summary stays as-is (each statement prefixed with `- `).
- No-op case: `No statements to execute (the state of Snowflake objects matches the Permifrost spec)`

### 6. Inspector warnings

- Warning messages in `inspector.py` switch from `console.log()` to `console.print()` with a `[yellow]Warning:[/yellow]` prefix (normal capitalization, not all-caps).

## Target output

A dry-run after all changes:

```
⚠ DRY RUN — no changes will be applied

Loaded 7 environment variables from /home/lui/.../gemma-sandbox-snowflake/.env

Manage Snowflake objects started
Resolving warehouse objects
Resolving database objects
Warning: Skipping metadata retrieval for user admin: Permifrost user doesn't have DESCRIBE privileges on this object
Warning: Skipping metadata retrieval for user snowflake: Permifrost user doesn't have DESCRIBE privileges on this object
Resolving user objects
Resolving role objects
Resolving schema objects

DDL statements to be executed:
3 CREATE, 2 ALTER (1 SET, 1 UNSET), 0 DROP

- USE ROLE SYSADMIN; CREATE WAREHOUSE ...
- USE ROLE SYSADMIN; CREATE DATABASE ...
- USE ROLE SYSADMIN; CREATE SCHEMA ...
- USE ROLE SECURITYADMIN; ALTER USER foo SET rsa_public_key='...'
- USE ROLE SECURITYADMIN; ALTER USER bar UNSET rsa_public_key

Manage Snowflake objects completed successfully

Permifrost started
Running command:
permifrost run permifrost.yml --ignore-missing-entities-dry-run --dry

[permifrost output...]

Permifrost completed successfully
```

## Validation strategy

After each implementation task:

1. Run existing tests: `uv run pytest -v`
2. Run a dry-run against the sandbox: `cd /home/lui/projects/internal/gemma-sandbox-snowflake && uv run --project /home/lui/projects/internal/tundri tundri run --dry -p permifrost.yml`

## Files affected

| File | Changes |
|------|---------|
| `tundri/cli.py` | Section headers, dry-run banner placement, `console.log` → `console.print` |
| `tundri/core.py` | Summary line builder, DDL grouping, DROP coloring, `console.log` → `console.print` |
| `tundri/utils.py` | Env loading condensed, dry-run banner restyled, `console.log` → `console.print` |
| `tundri/inspector.py` | Warning format, `console.log` → `console.print` |

No new files or modules created.
