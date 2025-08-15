#!/bin/bash

# Script to bump version across all files
# Usage: ./scripts/bump_version.sh [patch|minor|major|version]

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 [patch|minor|major|version]"
    echo "  patch:  bump patch version (0.1.0 -> 0.1.1)"
    echo "  minor:  bump minor version (0.1.0 -> 0.2.0)"
    echo "  major:  bump major version (0.1.0 -> 1.0.0)"
    echo "  version: specify exact version (e.g., 0.1.2)"
    exit 1
fi

BUMP_TYPE=$1

# Get current version
CURRENT_VERSION=$(cat VERSION)
echo "Current version: $CURRENT_VERSION"

# Calculate new version
if [ "$BUMP_TYPE" = "patch" ] || [ "$BUMP_TYPE" = "minor" ] || [ "$BUMP_TYPE" = "major" ]; then
    # Use bumpversion to calculate new version
    NEW_VERSION=$(bumpversion --dry-run --list $BUMP_TYPE | grep new_version | cut -d= -f2)
else
    # Use specified version
    NEW_VERSION=$BUMP_TYPE
fi

echo "New version: $NEW_VERSION"

# Confirm
read -p "Do you want to bump version from $CURRENT_VERSION to $NEW_VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Version bump cancelled."
    exit 1
fi

# Update files
echo "Updating version files..."

# Update VERSION file
echo "$NEW_VERSION" > VERSION

# Update .bumpversion.cfg
sed -i "s/current_version = .*/current_version = $NEW_VERSION/" .bumpversion.cfg

# Update src/permifrost/__init__.py
sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" src/permifrost/__init__.py

# Update pyproject.toml
sed -i "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

echo "✅ Version bumped to $NEW_VERSION"
echo ""
echo "Files updated:"
echo "  - VERSION"
echo "  - .bumpversion.cfg"
echo "  - src/permifrost/__init__.py"
echo "  - pyproject.toml"
echo ""
echo "Next steps:"
echo "  1. Commit the changes:"
echo "     git add VERSION .bumpversion.cfg src/permifrost/__init__.py pyproject.toml"
echo "     git commit -m \"Bump version to $NEW_VERSION\""
echo ""
echo "  2. Push to trigger GitHub Actions:"
echo "     git push origin <your-branch>"
echo ""
echo "  3. Create a Pull Request to trigger Test PyPI release"
