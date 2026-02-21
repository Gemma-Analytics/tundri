# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Permifrost

Permifrost is a Python CLI tool that manages Snowflake database permissions declaratively. Given a YAML spec file describing the desired permission state (roles, users, databases, warehouses, schemas), it connects to Snowflake and generates/executes the necessary `GRANT` and `REVOKE` SQL statements to match the spec.

**This is a fork by Gemma Analytics** of the original Permifrost project maintained by GitLab Data. The upstream source is at [https://gitlab.com/gitlab-data/permifrost](https://gitlab.com/gitlab-data/permifrost). Gemma Analytics maintains this fork as `gemma.permifrost` on PyPI for use with [tundri](https://github.com/Gemma-Analytics/tundri) — a custom tool that handles CREATE/DROP/ALTER DDL operations on Snowflake objects and then delegates permission grants to Permifrost.

## Development Commands

```bash
# Install dev dependencies
pip install -e '.[dev]'

# Full setup with pre-commit hooks
make initial-setup

# Run tests (via Docker)
make test

# Run tests locally (inside Docker shell or with dev install)
pytest -x -v --disable-pytest-warnings

# Type checking
make typecheck

# Linting (format + type check + flake8)
make local-lint

# Show lint results without auto-fixing
make local-show-lint

# Open interactive Docker shell with local Permifrost installed
make permifrost
```

## Architecture

### Module Overview

| Module | Purpose |
|--------|---------|
| `src/permifrost/cli/cli.py` | Click CLI entry point (`permifrost` command group) |
| `src/permifrost/cli/permissions.py` | `run` and `spec-test` subcommands |
| `src/permifrost/snowflake_connector.py` | Snowflake connection management |
| `src/permifrost/snowflake_spec_loader.py` | Load and validate YAML spec into internal objects |
| `src/permifrost/snowflake_permission.py` | Generate GRANT/REVOKE SQL statements |
| `src/permifrost/snowflake_grants.py` | Query current Snowflake grants |
| `src/permifrost/snowflake_role_grant_checker.py` | Check role membership grants |
| `src/permifrost/spec_file_loader.py` | Raw YAML file loading |
| `src/permifrost/spec_schemas/snowflake.py` | Schema validation for the spec file |
| `src/permifrost/entities.py` | Internal data models for spec entities |
| `src/permifrost/types.py` | Type definitions |
| `src/permifrost/error.py` | Custom exception classes |
| `src/permifrost/logger.py` | Logging setup |

### Execution Flow

1. Load YAML spec file and validate against schema
2. Connect to Snowflake using env vars (SECURITYADMIN role required)
3. Query current Snowflake grants for the roles/users in scope
4. Diff desired state (spec) vs current state (Snowflake)
5. Generate GRANT/REVOKE SQL statements
6. Execute statements (or print them in `--dry` mode)

### Permission Model

All permissions are expressed as `read` or `write`, with Permifrost generating the appropriate Snowflake grants:

| Object | `read` grants | `write` grants |
|--------|--------------|----------------|
| Database | `USAGE` | `MONITOR`, `CREATE SCHEMA` |
| Schema | `USAGE` | `MONITOR`, `CREATE TABLE`, `CREATE VIEW`, etc. |
| Table/View | `SELECT` | `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `REFERENCES` |

## Connection Parameters

Required environment variables:

```bash
PERMISSION_BOT_USER=<user>
PERMISSION_BOT_ACCOUNT=<account-id>
PERMISSION_BOT_WAREHOUSE=<warehouse>
```

Authentication options (choose one):

```bash
# Username/password
PERMISSION_BOT_PASSWORD=<password>
PERMISSION_BOT_DATABASE=<database>
PERMISSION_BOT_ROLE=SECURITYADMIN

# OAuth
PERMISSION_BOT_OAUTH_TOKEN=<token>

# Key pair
PERMISSION_BOT_KEY_PATH=/path/to/key.p8
PERMISSION_BOT_KEY_PASSPHRASE=<passphrase>

# External browser SSO
PERMISSION_BOT_AUTHENTICATOR=externalbrowser
```

Permifrost requires the `SECURITYADMIN` role and will fail validation if a different role is used.

## Key Files

- `src/permifrost/` — main package source
- `tests/` — test suite
- `setup.cfg` / `pyproject.toml` — package configuration
- `VERSION` — current package version (also in `src/permifrost/__init__.py`)
- `CHANGELOG.md` — release history
- `GEMMA_RELEASE.md` — Gemma Analytics PyPI release guide
- `Makefile` — development workflow commands
- `docker-compose.yml` / `docker/` — Docker-based dev environment

## Conventions

- The package is published to PyPI as `gemma.permifrost` (not the upstream `permifrost`)
- Python >=3.8 required
- Code quality: `black` (formatting), `isort` (import sorting), `flake8` (linting), `mypy` (type checking)
- Pre-commit hooks run on `pre-commit` and `pre-push` stages
- Do **not** use forward slashes in branch names (CI limitation from upstream)
- Never commit directly to `main` — always create a feature branch and open a PR

## Releasing

Version bumping uses `bumpversion`. See `GEMMA_RELEASE.md` for the full PyPI release process.

```bash
# Bump version and tag
make release type=patch   # or minor, major
```
