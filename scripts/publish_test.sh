#!/bin/bash

# Script to publish gemma.permifrost to Test PyPI
# Usage: ./scripts/publish_test.sh

set -e

echo "🚀 Publishing gemma.permifrost to Test PyPI..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Not in a virtual environment. Consider activating one."
fi

# Install build tools if not present
echo "📦 Installing build tools..."
pip install --upgrade build twine

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build the package
echo "🔨 Building package..."
python -m build

# Check the built package
echo "🔍 Checking built package..."
twine check dist/*

# Upload to Test PyPI
echo "📤 Uploading to Test PyPI..."
echo "You will be prompted for your Test PyPI credentials."
echo "Username: __token__"
echo "Password: Your Test PyPI API token (starts with pypi-)"
twine upload --repository testpypi dist/*

echo "✅ Successfully published to Test PyPI!"
echo "🔗 Test PyPI URL: https://test.pypi.org/project/gemma.permifrost/"
echo ""
echo "To install from Test PyPI:"
echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ gemma.permifrost"
