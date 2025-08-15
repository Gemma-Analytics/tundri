# Gemma Analytics Permifrost Release Guide

This guide explains how to release the `gemma.permifrost` package to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account on [PyPI](https://pypi.org/account/register/)
2. **Test PyPI Account**: Create an account on [Test PyPI](https://test.pypi.org/account/register/)
3. **API Tokens**: Generate API tokens for both PyPI and Test PyPI
   - Go to your account settings
   - Create a new API token
   - Copy the token (it starts with `pypi-`)

## Setup

1. **Configure credentials** (choose one method):

   **Method A: Environment Variables**
   ```bash
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=your_api_token_here
   ```

   **Method B: .pypirc file**
   ```bash
   # Edit .pypirc and replace YOUR_PYPI_API_TOKEN_HERE with your actual token
   cp .pypirc ~/.pypirc
   chmod 600 ~/.pypirc
   ```

2. **Install build tools**:
   ```bash
   pip install --upgrade build twine
   ```

## Release Process

### Step 1: Test Release to Test PyPI

1. **Update version** (if needed):
   ```bash
   # Update VERSION file
   echo "0.1.0" > VERSION
   
   # Update .bumpversion.cfg
   # Update src/permifrost/__init__.py
   ```

2. **Build and test locally**:
   ```bash
   # Clean previous builds
   rm -rf dist/ build/ *.egg-info/
   
   # Build package
   python -m build
   
   # Check package
   twine check dist/*
   ```

3. **Publish to Test PyPI**:
   ```bash
   ./scripts/publish_test.sh
   ```

4. **Test installation**:
   ```bash
   # Create a new virtual environment for testing
   python -m venv test_env
   source test_env/bin/activate
   
   # Install from Test PyPI
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ gemma.permifrost
   
   # Test the installation
   permifrost --help
   ```

### Step 2: Production Release to PyPI

1. **Verify everything works** from Test PyPI
2. **Publish to Production PyPI**:
   ```bash
   ./scripts/publish_prod.sh
   ```

3. **Verify the release**:
   - Check [PyPI project page](https://pypi.org/project/gemma.permifrost/)
   - Test installation: `pip install gemma.permifrost`

## Version Management

### Bumping Versions

Use the existing bumpversion setup:

```bash
# For patch release (0.1.0 -> 0.1.1)
bumpversion patch

# For minor release (0.1.0 -> 0.2.0)
bumpversion minor

# For major release (0.1.0 -> 1.0.0)
bumpversion major
```

### Manual Version Updates

If you need to manually update versions:

1. Update `VERSION` file
2. Update `.bumpversion.cfg` current_version
3. Update `src/permifrost/__init__.py` __version__
4. Update `pyproject.toml` version

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Ensure your API token is correct
   - Check that `.pypirc` has correct permissions (600)
   - Verify environment variables are set

2. **Package Name Conflicts**:
   - The package name `gemma.permifrost` should be unique
   - If there's a conflict, consider using a different name

3. **Build Errors**:
   - Ensure all dependencies are installed
   - Check that `pyproject.toml` is properly formatted
   - Verify all required files are included in `MANIFEST.in`

### Testing Before Release

```bash
# Test build
python -m build

# Test package check
twine check dist/*

# Test upload to Test PyPI (dry run)
twine upload --repository testpypi --dry-run dist/*
```

## Package Information

- **Package Name**: `gemma.permifrost`
- **Description**: Permifrost Permissions - Fork by Gemma Analytics
- **Author**: Gemma Analytics
- **License**: MIT
- **Python Version**: >=3.8
- **Entry Point**: `permifrost` command

## Links

- [PyPI Project](https://pypi.org/project/gemma.permifrost/)
- [Test PyPI Project](https://test.pypi.org/project/gemma.permifrost/)
- [GitHub Repository](https://github.com/Gemma-Analytics/permifrost)
