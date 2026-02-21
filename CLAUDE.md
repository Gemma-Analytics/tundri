# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Tundri

Tundri is a Python CLI tool that manages Snowflake database objects and permissions declaratively. It reads Permifrost YAML specification files, compares the desired state with the actual Snowflake account state, and generates/executes DDL statements (CREATE/DROP/ALTER) for objects. After object management, it runs Permifrost to handle permission grants.

Gemma's fork of Permifrost is primarily used via [Tundri](https://github.com/Gemma-Analytics/tundri/tree/main/tundri) — a custom wrapper tool that handles the CREATE/DROP/ALTER DDL operations on Snowflake objects before delegating permission grants to Permifrost.

## Development Commands

```bash
# Install dependencies
uv sync

# Run CLI
uv run tundri run --dry -p examples/permifrost.yml   # Dry run
uv run tundri run -p examples/permifrost.yml          # Execute

# Subcommands
uv run tundri drop_create -p spec.yml --dry   # Objects only (skip Permifrost)
uv run tundri permifrost -p spec.yml          # Permissions only (skip objects)

# Tests
uv run pytest -v                              # All tests
uv run pytest -v tests/integration_tests/     # Integration tests only

# Format
uv run black .
```

## Architecture

### Module Overview

| Module | Purpose |
|--------|---------|
| `cli.py` | Click CLI entry point with `run`, `drop_create`, `permifrost` subcommands |
| `core.py` | Main logic: inspect, compare, generate DDL, execute |
| `parser.py` | Parse Permifrost YAML specs into `SnowflakeObject` instances |
| `inspector.py` | Query Snowflake metadata via `SHOW` and `DESCRIBE` commands |
| `objects.py` | Frozen dataclasses for Snowflake objects (Warehouse, Database, Role, User, Schema) |
| `constants.py` | Object type mappings, system roles, role hierarchy |
| `utils.py` | Snowflake connection, env var loading, parameter formatting |

### Execution Flow

1. Parse Permifrost YAML spec into desired object state
2. Inspect current Snowflake account state
3. Compare: generate DROP, CREATE, ALTER statements
4. Execute DDL (with confirmation unless `--dry` or CI)
5. Run Permifrost for permission grants

### Snowflake Role Model

- **SYSADMIN**: Used for object operations (databases, warehouses, schemas)
- **SECURITYADMIN**: Used for user/role operations and metadata inspection
- System roles (`ACCOUNTADMIN`, `SECURITYADMIN`, `SYSADMIN`, `USERADMIN`, `ORGADMIN`) are never created/dropped

### Safety

- Schemas are never dropped (only created)
- Dry-run mode shows changes without executing
- Account identifier confirmation before destructive operations
- Auto-skip confirmations in CI (`CI=true`)

## Environment Variables

Required (in `.env` next to spec file):
```
PERMISSION_BOT_ACCOUNT=<account-id>
PERMISSION_BOT_USER=PERMIFROST
PERMISSION_BOT_PASSWORD=<password>       # or use key auth
PERMISSION_BOT_ROLE=SECURITYADMIN
PERMISSION_BOT_DATABASE=PERMIFROST
PERMISSION_BOT_WAREHOUSE=ADMIN
```

Optional key auth:
```
PERMISSION_BOT_KEY_PATH=/path/to/key.p8
PERMISSION_BOT_KEY_PASSPHRASE=<passphrase>
```

## Key Files

- `pyproject.toml` — version, dependencies, CLI entry point
- `examples/permifrost.yml` — example Permifrost spec
- `docs/RELEASE_WORKFLOW.md` — release process details
- `tundri/constants.py` — system roles, object type mappings

## Conventions

- Use `uv` for all Python operations (never `pip` or `python` directly)
- Type hints throughout
- Frozen dataclasses for Snowflake objects with custom equality (type + name, case-insensitive)
- `ought_*` prefix for desired state, `existing_*` for current state
- `is_` prefix for boolean flags
- Rich console for styled output
- Never commit directly to `main` — always create a feature branch and open a PR

## Version & Release

- Version in `pyproject.toml`
- Release via GitHub Actions: manual trigger -> version bump -> PR -> merge -> tag -> PyPI publish
