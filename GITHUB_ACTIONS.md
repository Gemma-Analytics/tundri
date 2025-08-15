# GitHub Actions Workflows for gemma.permifrost

This document explains the automated release workflows for the `gemma.permifrost` package.

## Overview

We have three GitHub Actions workflows that handle different aspects of the release process:

1. **Test Workflow** (`test.yml`) - Runs tests and checks before releases
2. **Release Workflow** (`release.yml`) - Automatically releases to Test PyPI and Production PyPI
3. **Manual Release Workflow** (`manual-release.yml`) - Allows manual releases via GitHub UI

## Workflow Details

### 1. Test Workflow (`test.yml`)

**Triggers:**
- Pull requests that modify `VERSION`, `src/`, `tests/`, `setup.py`, or `pyproject.toml`
- Pushes to `main`/`master` that modify the same files

**What it does:**
- Runs tests on multiple Python versions (3.8, 3.9, 3.10, 3.11)
- Performs linting checks (flake8, isort, black)
- Runs type checking with mypy
- Executes pytest with coverage
- Tests package building and installation
- Uploads build artifacts for inspection

### 2. Release Workflow (`release.yml`)

**Triggers:**
- Pull requests that modify `VERSION` file
- Pushes to `main`/`master` that modify `VERSION` file

**Jobs:**

#### Test Release Job
- **When:** PR is opened/updated with VERSION changes
- **What:** Publishes to Test PyPI
- **Features:**
  - Only runs if VERSION file actually changed
  - Builds and validates the package
  - Publishes to Test PyPI
  - Comments on the PR with installation instructions
  - Uses `skip-existing: true` to avoid conflicts

#### Production Release Job
- **When:** PR with VERSION changes is merged to main/master
- **What:** Publishes to Production PyPI
- **Features:**
  - Only runs if VERSION file actually changed
  - Builds and validates the package
  - Publishes to Production PyPI
  - Creates a GitHub release with tag
  - Uses `skip-existing: true` to avoid conflicts

### 3. Manual Release Workflow (`manual-release.yml`)

**Triggers:**
- Manual trigger via GitHub Actions UI

**Features:**
- Allows specifying version and target (test/production)
- Updates all version files automatically
- Commits and tags the changes
- Creates GitHub releases for production releases

## Setup Instructions

### 1. Repository Secrets

You need to set up the following secrets in your GitHub repository:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add the following secrets:

#### Required Secrets:
- `TEST_PYPI_API_TOKEN` - Your Test PyPI API token (starts with `pypi-`)
- `PYPI_API_TOKEN` - Your Production PyPI API token (starts with `pypi-`)

#### Optional Secrets:
- `GITHUB_TOKEN` - Automatically provided by GitHub

### 2. Getting PyPI API Tokens

#### Test PyPI Token:
1. Go to [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/)
2. Create an account if you don't have one
3. Go to Account Settings → API tokens
4. Create a new token with "Entire account" scope
5. Copy the token (starts with `pypi-`)

#### Production PyPI Token:
1. Go to [https://pypi.org/account/register/](https://pypi.org/account/register/)
2. Create an account if you don't have one
3. Go to Account Settings → API tokens
4. Create a new token with "Entire account" scope
5. Copy the token (starts with `pypi-`)

### 3. Branch Protection (Recommended)

Set up branch protection for `main`/`master`:

1. Go to Settings → Branches
2. Add rule for `main`/`master`
3. Enable:
   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Select the "test" workflow as required

## Usage Examples

### Automatic Release Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/new-version
   ```

2. **Update VERSION file:**
   ```bash
   echo "0.1.1" > VERSION
   git add VERSION
   git commit -m "Bump version to 0.1.1"
   git push origin feature/new-version
   ```

3. **Create a Pull Request:**
   - The test workflow will run automatically
   - If VERSION changed, it will publish to Test PyPI
   - A comment will be added to the PR with installation instructions

4. **Merge the PR:**
   - The production workflow will run automatically
   - If VERSION changed, it will publish to Production PyPI
   - A GitHub release will be created

### Manual Release

1. Go to Actions → Manual Release
2. Click "Run workflow"
3. Enter the version (e.g., "0.1.2")
4. Select target (test or production)
5. Click "Run workflow"

## Workflow Behavior

### VERSION File Detection

The workflows use git diff to detect if the VERSION file actually changed:

- **For PRs:** Compares base branch with PR branch
- **For pushes:** Compares current commit with previous commit

This prevents unnecessary releases when VERSION hasn't changed.

### Skip Existing

All PyPI uploads use `skip-existing: true`, which means:
- If a version already exists on PyPI, the upload will be skipped
- No errors will occur for duplicate versions
- Useful for re-running workflows

### Error Handling

- Build failures will stop the workflow
- PyPI upload failures will be reported
- Test failures will prevent releases
- All steps have proper error reporting

## Monitoring

### Workflow Status

- Check the Actions tab in your repository
- Green checkmarks indicate success
- Red X marks indicate failures
- Click on any workflow run for detailed logs

### Release Tracking

- Test releases: Check Test PyPI project page
- Production releases: Check PyPI project page
- GitHub releases: Check the Releases tab

## Troubleshooting

### Common Issues

1. **Authentication Errors:**
   - Verify API tokens are correct
   - Ensure tokens have upload permissions
   - Check that secrets are properly set

2. **Version Conflicts:**
   - The workflow uses `skip-existing: true` to handle duplicates
   - If you need to force upload, manually delete the version from PyPI first

3. **Build Failures:**
   - Check the build logs for specific errors
   - Ensure all dependencies are properly specified
   - Verify package structure is correct

4. **Test Failures:**
   - Fix any linting issues (flake8, isort, black)
   - Address mypy type checking errors
   - Fix failing tests

### Debugging

- All workflows provide detailed logs
- Check the "Actions" tab for workflow runs
- Look for specific error messages in the logs
- Use the manual release workflow for testing

## Security Considerations

- API tokens are stored as GitHub secrets
- Tokens should have minimal required permissions
- Consider using scoped tokens for production
- Regularly rotate API tokens
- Monitor PyPI for unauthorized uploads

## Best Practices

1. **Version Management:**
   - Always update VERSION file for releases
   - Use semantic versioning
   - Keep version files in sync

2. **Testing:**
   - Test locally before pushing
   - Use Test PyPI for validation
   - Verify installation works

3. **Documentation:**
   - Update CHANGELOG.md for releases
   - Document breaking changes
   - Keep release notes current

4. **Monitoring:**
   - Check workflow status regularly
   - Monitor PyPI for successful uploads
   - Verify GitHub releases are created
