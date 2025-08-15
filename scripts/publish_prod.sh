#!/bin/bash

# Script to publish gemma.permifrost to Production PyPI
# Usage: ./scripts/publish_prod.sh

set -e

echo "🚀 Publishing gemma.permifrost to Production PyPI..."

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

# Confirm before uploading to production
echo "⚠️  WARNING: You are about to publish to PRODUCTION PyPI!"
echo "This will make the package publicly available."
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Publishing cancelled."
    exit 1
fi

# Upload to Production PyPI
echo "📤 Uploading to Production PyPI..."
echo "You will be prompted for your PyPI credentials."
echo "Username: __token__"
echo "Password: Your PyPI API token (starts with pypi-)"
twine upload dist/*

echo "✅ Successfully published to Production PyPI!"
echo "🔗 PyPI URL: https://pypi.org/project/gemma.permifrost/"
echo ""
echo "To install from PyPI:"
echo "pip install gemma.permifrost"
