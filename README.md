<div align="center">
  <img src="docs/images/logo.jpg" alt="Snowflake Manager Logo" width="200">
</div>

**tundri** is a Python package to declaratively create, drop, and alter Snowflake objects and manage their permissions with [Permifrost](https://gitlab.com/gitlab-data/permifrost).

## Motivation

Permifrost is great at managing permissions, but it doesn't create or alter objects. As [GitLab's data team handbook](https://handbook.gitlab.com/handbook/enterprise-data/platform/permifrost/) states:
> Object creation and deletion is not managed by permifrost

tundri reads the Permifrost spec file and compares with the current state of the Snowflake account. It then creates, drops, and alters the objects to match the spec file. It does so by leveraging Permifrost's YAML `meta` tags. Once the objects are created, tundri runs Permifrost to set the permissions.

## Getting started

### Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Credentials to a Snowflake account with the `securityadmin` role
- A Permifrost spec file

### Install

With uv:
```bash
uv add tundri
```

With pip:
```bash
pip install tundri
```

### Configure

#### Permifrost
Add a valid Permifrost spec file to your repository. You can use the example provided in the `examples` folder.

#### Snowflake
Set up your Snowflake connection details in the environment variables listed below.

> [!TIP]
> You can use a `.env` file to store your credentials.

```bash
PERMISSION_BOT_ACCOUNT=abc134.west-europe.azure  # Your account identifier
PERMISSION_BOT_USER=PERMIFROST
PERMISSION_BOT_PASSWORD=...
PERMISSION_BOT_ROLE=SECURITYADMIN    # Permifrost requires it to be `SECURITYADMIN`
PERMISSION_BOT_DATABASE=PERMIFROST
PERMISSION_BOT_WAREHOUSE=ADMIN
```

### Usage
The `run` subcommand is going to drop/create objects and run Permifrost.

#### Dry run
```bash
tundri run --permifrost_spec_path examples/permifrost.yml --dry
```

#### Normal run
```bash
tundri run --permifrost_spec_path examples/permifrost.yml
```

## Development
### Local setup
Install the development dependencies

```bash
uv sync
```

### Run tests
Run the tests
```bash
uv run pytest -v
```

### Formatting
Run the command below to format the code
```bash
uv run black .
```