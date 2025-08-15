<div align="center">
  <img src="docs/images/logo.jpg" alt="tundri Logo" width="200">
</div>

**tundri** is a Python package to declaratively create, drop, and alter Snowflake objects and manage their permissions with [Permifrost](https://gitlab.com/gitlab-data/permifrost).

## Motivation

Permifrost is great at managing permissions, but it doesn't create or alter objects. As [GitLab's data team handbook](https://handbook.gitlab.com/handbook/enterprise-data/platform/permifrost/) states:
> Object creation and deletion is not managed by permifrost

With only Permifrost, one would have to manually create the objects and then run Permifrost to set the permissions. This is error prone and time consuming. That is where tundri comes in.

### In a nutshell
**tundri** reads the [Permifrost spec file](https://gitlab.com/gitlab-data/permifrost#spec_file) and compares with the current state of the Snowflake account. It then creates, drops, and alters the objects to match. It leverages Permifrost's YAML `meta` tags to set attributes like `default_role` for users and `warehouse_size` for warehouses. Once the objects are created, tundri runs Permifrost to set the permissions.

## Getting started

### Prerequisites

- Credentials to a Snowflake account with the `securityadmin` role
- A Permifrost spec file

### Install

```bash
pip install tundri
```

### Configure

#### Permifrost
Add a valid [Permifrost spec file](https://gitlab.com/gitlab-data/permifrost#spec_file) to your repository. You can use the files in the `examples` folder as reference.

#### Snowflake
Set up your Snowflake connection details in the environment variables listed below.

> [!TIP]
> You can use a `.env` file to store your credentials. Place it in the same folder as the Permifrost spec file.

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

#### Getting help
```bash
tundri --help
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

### Testing locally
Dry run with the example spec file
```bash
uv run tundri run --dry -p examples/permifrost.yml
```

## Contributing

### Release process

The release process is automated using GitHub Actions. Here's how it works:

1. **Adding new features or bug fixes**
   - PR tests run automatically to verify the changes on each PR
   - The package is published to TestPyPI for testing
   - Multiple PRs can be merged to main until a release-ready state is reached

1. **Initiating a Release**
   - A maintainer triggers the manual release workflow
   - They specify the version bump type (`major`, `minor`, or `patch`)
   - This creates a release branch and PR with updated version

1. **Release Creation**
   - When the release PR is merged to main:
     - A Git tag is created (e.g., `v1.2.3`)
     - A GitHub release is created
     - The package is published to PyPI

The process requires the following GitHub secrets to be configured:
- `PYPI_API_TOKEN`: For production PyPI publishing
- `TEST_PYPI_API_TOKEN`: For TestPyPI publishing
- `SNOWFLAKE_USER`: For running tests

For full details on the release workflow, see [RELEASE_WORKFLOW.md](docs/RELEASE_WORKFLOW.md).
