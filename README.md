<div align="center">
  <img src="docs/images/logo.jpg" alt="Snowflake Manager Logo" width="200">
</div>

**tundri** is a Python package to declaratively create, drop, and alter Snowflake objects and manage their permissions with [Permifrost](https://gitlab.com/gitlab-data/permifrost)

## How to use
The `run` subcommand is going to drop/create objects and run Permifrost.

### Dry run

```bash
tundri run --permifrost_spec_path examples/permifrost.yml --dry
```

### Normal run
```bash
tundri run --permifrost_spec_path examples/permifrost.yml
```

## Setup

### Install
Create virtual environment, activate and upgrade `pip`
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

Install from the GitHub repository
```bash
pip install git+https://github.com/Gemma-Analytics/snowflake-manager.git
```

> Note: you can specify a tag to install a specific version:
> 
> ```bash
> pip install git+https://github.com/Gemma-Analytics/snowflake-manager.git@v1.0.0
> ```

## Configure

### Permifrost
Add a valid Permifrost spec file to your repository. You can use the example provided in the `examples` folder.

### Snowflake requirements
You need to have a user with `securityadmin` and `sysadmin` roles.

### Environment variables

Set up your Snowflake connection details in the environment variables listed below. 
```bash
PERMISSION_BOT_ACCOUNT=abc134.west-europe.azure  # Your account identifier
PERMISSION_BOT_USER=PERMIFROST
PERMISSION_BOT_PASSWORD=...
PERMISSION_BOT_ROLE=SECURITYADMIN    # Permifrost requires it to be `SECURITYADMIN`
PERMISSION_BOT_DATABASE=PERMIFROST
PERMISSION_BOT_WAREHOUSE=ADMIN
```

**Note:**
It is encouraged to use a .env file to store secrets and environment variables locally
- The .env file has to live in the same folder as the Permifrost spec file
- Snowflake-manager only parses files that are called ".env"; if the file that stores 
your secrets has a different name, Snowflake-manager will ignore it

Snowflake-manager automatically checks the folder, where the Permifrost spec file lives,
for a .env file, and parses it. If no .env file exists locally, Snowflake-manager will
fall back to the system's environment variables. If an environment variables exists in
both, the .env file and the system's environment variables, environment variables in the
.env file will take precedence (i.e., Snowflake-manager will override the system's
environment variable with the same name)

## Develop

### Pre-release integration test
> **Attention**: we currently use a manual process to test new releases that is only applicable to Gemma's internal infrastructure

Before merging changes to `main`, please test the changes using the `develop` branch. Steps:

- Create a new branch for the new feature e.g. `my-new-feature`
- When finished, create a PR with `develop` branch as the base branch
- Merge the PR into `develop` branch
- In Gemma's best practices repo, merge a dummy change on `permifrost.yml` to trigger the CI/CD pipelines (they are configured to install `snowflake-manager` from the `develop` branch)
- If both the PR (dry run) and merge to main (normal run) pipelines work, proceed to create a new PR in this repo from branch `develop` to `main`
- Once the PR from `develop` to `main` is merged, the changes will be available to all clients 

### Local setup

Install the development dependencies

```bash
pip install -r requirements-dev.txt
```

Install the package locally in editable mode

```bash
pip install --editable .
```
Then you will be able to edit the code and run the CLI to test changes immediately.

### Unit tests
You should run the unit tests after changing the code:
```bash
pytest
```
Likewise, whenever a new functionality is implemented, a new test for it should be added.

### Formatting
Please run the command below to format the code
```bash
black .
```