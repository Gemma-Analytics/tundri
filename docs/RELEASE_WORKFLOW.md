# Release Workflow and PyPI Publishing

This document explains how the automated release and PyPI publishing workflow works for the `tundri` package.

## Overview

The project uses GitHub Actions to automate the release process and PyPI publishing. The workflow consists of several components:

1. **Manual Release Workflow** - Creates release branches and PRs
2. **PR Tests** - Runs tests on pull requests
3. **TestPyPI Publishing** - Publishes to TestPyPI for testing
4. **Release Merge Workflow** - Creates tags and releases when PRs are merged
5. **PyPI Publishing** - Publishes to production PyPI when releases are created

## Workflow Files

### 1. Manual Release (`manual-release.yml`)

**Trigger**: Manual workflow dispatch

**Purpose**: Creates a new release branch and PR with an incremented version number.

**Inputs**:
- `version_type`: Type of version bump (`major`, `minor`, `patch`)

**Process**:
1. Reads current version from `pyproject.toml`
2. Calculates new version based on bump type
3. Updates `pyproject.toml` with new version
4. Creates a release branch (`release/vX.Y.Z`)
5. Creates a pull request to merge the release branch

### 2. PR Tests (`pr-tests.yml`)

**Trigger**: Pull requests to `main` branch

**Purpose**: Runs unit tests and integration tests.

**Process**:
1. Sets up Python 3.12 environment
2. Installs `uv` package manager
3. Installs dependencies with `uv sync`
4. Runs tests with `uv run pytest -vv`

### 3. TestPyPI Publishing (`publish-to-testpypi.yml`)

**Trigger**: Pull requests to `main` branch (when not merged)

**Purpose**: Publishes package to TestPyPI for testing.

**Process**:
1. Builds the package
2. Validates the package with `twine check`
3. Publishes to TestPyPI
4. Comments on the PR with installation instructions

### 4. Release Merge (`on-release-merge.yml`)

**Trigger**: Pull requests merged to `main` (only release branches)

**Purpose**: Creates Git tags and GitHub releases.

**Process**:
1. Creates a Git tag (`vX.Y.Z`)
2. Creates a GitHub release
3. Publishes to PyPI (production)

### 5. PyPI Publishing (`publish-on-release.yml`)

**Trigger**: GitHub releases published

**Purpose**: Publishes package to production PyPI.

**Process**:
1. Builds the package
2. Validates the package
3. Publishes to PyPI

## Required Secrets

The following GitHub secrets must be configured:

### For PyPI Publishing
- `PYPI_API_TOKEN`: API token for PyPI (production)

### For TestPyPI Publishing
- `TEST_PYPI_API_TOKEN`: API token for TestPyPI

### For Testing
- `SNOWFLAKE_USER`: Snowflake username
- `SNOWFLAKE_PRIVATE_KEY`: Private key for Snowflake authentication
- `SNOWFLAKE_KEY_PASSPHRASE`: Private key passphrase (leave empty if not used)
- `SNOWFLAKE_ACCOUNT`: Snowflake account identifier
- `SNOWFLAKE_DATABASE`: Snowflake database name
- `SNOWFLAKE_ROLE`: Snowflake role name
- `SNOWFLAKE_WAREHOUSE`: Snowflake warehouse name

## How to Create a Release

### Option 1: Manual Release (Recommended)

1. Go to the **Actions** tab in GitHub
2. Select **Manual Release** workflow
3. Click **Run workflow**
4. Choose the version bump type:
   - `patch`: Bug fixes (1.3.0 → 1.3.1)
   - `minor`: New features (1.3.0 → 1.4.0)
   - `major`: Breaking changes (1.3.0 → 2.0.0)
5. Click **Run workflow**
6. Review the created pull request
7. Merge the pull request when ready

### Option 2: Manual Process

1. Update the version in `pyproject.toml`
2. Create a release branch: `git checkout -b release/vX.Y.Z`
3. Commit and push: `git push origin release/vX.Y.Z`
4. Create a pull request
5. Merge the pull request

## Version Management

Versions are managed in `pyproject.toml`:

```toml
[project]
version = "1.3.0"
```

The workflow automatically:
- Reads the current version
- Calculates the new version based on the bump type
- Updates the file
- Creates appropriate Git tags

## Publishing Process

### TestPyPI (Testing)
- Automatically publishes on pull requests
- Allows testing before production release
- Comments on PR with installation instructions

### PyPI (Production)
- Publishes when release branches are merged
- Publishes when GitHub releases are created
- Requires proper API tokens

## Testing the Release

### From TestPyPI
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ tundri==X.Y.Z
```

### From PyPI (after release)
```bash
pip install tundri==X.Y.Z
```

## Troubleshooting

### Common Issues

1. **Version already exists**: PyPI doesn't allow overwriting versions. Increment the version number.

2. **Build failures**: Check that all dependencies are properly specified in `pyproject.toml`.

3. **Test failures**: Ensure all tests pass before creating a release.

4. **Authentication errors**: Verify that PyPI API tokens are correctly configured in GitHub secrets.

### Manual Override

If the automated workflow fails, you can manually publish:

```bash
# Build the package
python -m build

# Check the package
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Best Practices

1. **Always test on TestPyPI first** before publishing to production PyPI
2. **Use semantic versioning** for version numbers
3. **Write clear release notes** in GitHub releases
4. **Test the package installation** after publishing
5. **Monitor the GitHub Actions** for any failures
